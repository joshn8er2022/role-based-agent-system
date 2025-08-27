"""
Role-based Agent Manager for DSPY Boss
Manages creation, assignment, and lifecycle of role-based agents
"""

import asyncio
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
from loguru import logger
import uuid

from .models import (
    AgentConfig, AgentRoleType, AgentHierarchyLevel, AgentStatus,
    TaskDefinition, TaskStatus, PromptSignature, HumanPairing
)
from .task_manager import TaskManager
from .mcp import MCPManager
from .role_based_agents import (
    BaseRoleAgent, StandaloneAgent, HumanPairedAgent, HumanShadowAgent
)


class RoleBasedAgentManager:
    """Manages all role-based agents in the system"""
    
    def __init__(self, task_manager: TaskManager, mcp_manager: MCPManager):
        self.task_manager = task_manager
        self.mcp_manager = mcp_manager
        
        self.agents: Dict[str, BaseRoleAgent] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.prompt_signatures: Dict[str, PromptSignature] = {}
        
        # Agent management settings
        self.max_standalone_agents = 10
        self.max_paired_agents = 5
        self.max_shadow_agents = 3
        self.agent_spawn_threshold = 8
        
        # Boss agent reference
        self.boss_agent: Optional[StandaloneAgent] = None
        
        logger.info("RoleBasedAgentManager initialized")
    
    def load_agents(self, agent_configs: Dict[str, AgentConfig], 
                   prompt_signatures: Dict[str, PromptSignature]):
        """Load agent configurations and create agents"""
        self.agent_configs = agent_configs
        self.prompt_signatures = prompt_signatures
        
        # Create agents from configs
        for name, config in agent_configs.items():
            agent = self.create_agent(config)
            if agent and isinstance(agent, StandaloneAgent) and config.hierarchy_level == AgentHierarchyLevel.BOSS:
                self.boss_agent = agent
        
        logger.info(f"Loaded {len(self.agents)} role-based agents")
    
    def create_agent(self, config: AgentConfig) -> Optional[BaseRoleAgent]:
        """Create an agent based on its role type"""
        try:
            agent_class = self._get_agent_class(config.role_type)
            
            if config.role_type == AgentRoleType.STANDALONE_AGENT:
                agent = agent_class(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
            elif config.role_type == AgentRoleType.HUMAN_PAIRED:
                agent = agent_class(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
            elif config.role_type == AgentRoleType.HUMAN_SHADOW:
                agent = agent_class(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
            else:
                raise ValueError(f"Unknown agent role type: {config.role_type}")
            
            self.agents[config.id] = agent
            agent.start()
            
            logger.info(f"Created and started {config.role_type.value} agent: {config.name}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent {config.name}: {e}")
            return None
    
    def _get_agent_class(self, role_type: AgentRoleType) -> Type[BaseRoleAgent]:
        """Get the appropriate agent class for a role type"""
        agent_classes = {
            AgentRoleType.STANDALONE_AGENT: StandaloneAgent,
            AgentRoleType.HUMAN_PAIRED: HumanPairedAgent,
            AgentRoleType.HUMAN_SHADOW: HumanShadowAgent
        }
        
        return agent_classes[role_type]
    
    async def create_boss_agent(self, name: str = "Boss Agent", capabilities: List[str] = None) -> StandaloneAgent:
        """Create or get the boss agent"""
        if self.boss_agent:
            logger.info("Boss agent already exists")
            return self.boss_agent
        
        boss_config = AgentConfig(
            name=name,
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.BOSS,
            description="Primary decision-making and coordination agent",
            capabilities=capabilities or [
                "strategic_planning", "decision_making", "task_delegation",
                "system_coordination", "agent_management", "resource_allocation"
            ],
            max_concurrent_tasks=5,
            model_name="gpt-4-turbo-preview",
            prompt_signature="boss_agent"
        )
        
        boss_agent = self.create_agent(boss_config)
        if isinstance(boss_agent, StandaloneAgent):
            self.boss_agent = boss_agent
            logger.info("Created boss agent successfully")
            return boss_agent
        
        raise RuntimeError("Failed to create boss agent")
    
    async def create_sub_agent(self, name: str, capabilities: List[str] = None, 
                              parent_agent_id: str = None) -> StandaloneAgent:
        """Create a subordinate standalone agent"""
        if len(self._get_agents_by_type(AgentRoleType.STANDALONE_AGENT)) >= self.max_standalone_agents:
            logger.warning("Maximum number of standalone agents reached")
            return None
        
        sub_agent_config = AgentConfig(
            name=name,
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            parent_agent_id=parent_agent_id or (self.boss_agent.config.id if self.boss_agent else None),
            description=f"Subordinate agent for specialized tasks",
            capabilities=capabilities or ["task_execution", "data_processing", "analysis"],
            max_concurrent_tasks=3,
            model_name="gpt-3.5-turbo",
            prompt_signature="sub_agent"
        )
        
        agent = self.create_agent(sub_agent_config)
        if isinstance(agent, StandaloneAgent):
            logger.info(f"Created sub-agent: {name}")
            return agent
        
        raise RuntimeError(f"Failed to create sub-agent: {name}")
    
    async def create_human_paired_agent(self, name: str, human_pairing: HumanPairing,
                                       capabilities: List[str] = None) -> HumanPairedAgent:
        """Create a human-paired collaborative agent"""
        if len(self._get_agents_by_type(AgentRoleType.HUMAN_PAIRED)) >= self.max_paired_agents:
            logger.warning("Maximum number of human-paired agents reached")
            return None
        
        paired_config = AgentConfig(
            name=name,
            role_type=AgentRoleType.HUMAN_PAIRED,
            description=f"Collaborative agent paired with {human_pairing.human_name}",
            capabilities=capabilities or ["collaboration", "communication", "task_coordination"],
            human_pairing=human_pairing,
            max_concurrent_tasks=2,  # Lower since requires human interaction
            model_name="gpt-4",
            prompt_signature="human_paired"
        )
        
        agent = self.create_agent(paired_config)
        if isinstance(agent, HumanPairedAgent):
            logger.info(f"Created human-paired agent: {name} for {human_pairing.human_name}")
            return agent
        
        raise RuntimeError(f"Failed to create human-paired agent: {name}")
    
    async def create_human_shadow_agent(self, name: str, represented_human_id: str,
                                       represented_human_name: str, shadow_permissions: List[str],
                                       capabilities: List[str] = None) -> HumanShadowAgent:
        """Create a human shadow agent"""
        if len(self._get_agents_by_type(AgentRoleType.HUMAN_SHADOW)) >= self.max_shadow_agents:
            logger.warning("Maximum number of human-shadow agents reached")
            return None
        
        shadow_config = AgentConfig(
            name=name,
            role_type=AgentRoleType.HUMAN_SHADOW,
            description=f"Shadow agent representing {represented_human_name}",
            capabilities=capabilities or ["decision_making", "human_representation", "task_execution"],
            represented_human_id=represented_human_id,
            represented_human_name=represented_human_name,
            shadow_permissions=shadow_permissions,
            max_concurrent_tasks=3,
            model_name="gpt-4",
            prompt_signature="human_shadow"
        )
        
        agent = self.create_agent(shadow_config)
        if isinstance(agent, HumanShadowAgent):
            logger.info(f"Created human-shadow agent: {name} for {represented_human_name}")
            return agent
        
        raise RuntimeError(f"Failed to create human-shadow agent: {name}")
    
    def _get_agents_by_type(self, role_type: AgentRoleType) -> List[BaseRoleAgent]:
        """Get all agents of a specific role type"""
        return [agent for agent in self.agents.values() 
                if agent.config.role_type == role_type]
    
    def _get_agents_by_hierarchy(self, hierarchy_level: AgentHierarchyLevel) -> List[StandaloneAgent]:
        """Get all standalone agents of a specific hierarchy level"""
        return [agent for agent in self.agents.values() 
                if (isinstance(agent, StandaloneAgent) and 
                    agent.config.hierarchy_level == hierarchy_level)]
    
    async def assign_task_to_best_agent(self, task: TaskDefinition) -> Optional[BaseRoleAgent]:
        """Assign task to the most suitable available agent"""
        suitable_agents = []
        
        # Find agents that can handle the task
        for agent in self.agents.values():
            if await agent.can_accept_task(task):
                # Calculate suitability score
                score = await self._calculate_agent_suitability(agent, task)
                suitable_agents.append((agent, score))
        
        if not suitable_agents:
            # Try to create a new agent if workload is high
            new_agent = await self._try_create_agent_for_task(task)
            if new_agent and await new_agent.can_accept_task(task):
                suitable_agents.append((new_agent, 1.0))
        
        if not suitable_agents:
            logger.warning(f"No suitable agent found for task: {task.name}")
            return None
        
        # Sort by suitability score (higher is better)
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent = suitable_agents[0][0]
        
        # Assign task
        success = await best_agent.assign_task(task)
        if success:
            logger.info(f"Assigned task {task.name} to agent {best_agent.config.name}")
            return best_agent
        
        return None
    
    async def _calculate_agent_suitability(self, agent: BaseRoleAgent, task: TaskDefinition) -> float:
        """Calculate how suitable an agent is for a task"""
        score = 0.0
        
        # Base score for availability
        if agent.config.is_available:
            score += 1.0
        
        # Role type preference
        if hasattr(task, 'preferred_role_type'):
            if agent.config.role_type == task.preferred_role_type:
                score += 2.0
        
        # Hierarchy level preference for standalone agents
        if isinstance(agent, StandaloneAgent):
            if hasattr(task, 'requires_boss_level') and task.requires_boss_level:
                if agent.config.hierarchy_level == AgentHierarchyLevel.BOSS:
                    score += 3.0
            elif agent.config.hierarchy_level == AgentHierarchyLevel.SUB_AGENT:
                score += 1.0  # Prefer sub-agents for regular tasks
        
        # Capability matching
        task_capabilities = getattr(task, 'required_capabilities', [])
        if task_capabilities:
            matching_capabilities = set(agent.config.capabilities) & set(task_capabilities)
            if matching_capabilities:
                score += len(matching_capabilities) / len(task_capabilities) * 2.0
        
        # Performance history
        if agent.config.total_tasks_completed > 0:
            score += agent.config.performance_score * 2.0
        
        # Current workload (prefer less busy agents)
        workload_factor = 1.0 - (len(agent.current_tasks) / agent.config.max_concurrent_tasks)
        score += workload_factor
        
        # Human interaction requirements
        if hasattr(task, 'requires_human_interaction'):
            if task.requires_human_interaction:
                if agent.config.role_type in [AgentRoleType.HUMAN_PAIRED, AgentRoleType.HUMAN_SHADOW]:
                    score += 2.0
            else:
                if agent.config.role_type == AgentRoleType.STANDALONE_AGENT:
                    score += 1.0
        
        return score
    
    async def _try_create_agent_for_task(self, task: TaskDefinition) -> Optional[BaseRoleAgent]:
        """Try to create a new agent to handle the task if workload is high"""
        current_workload = len([agent for agent in self.agents.values() 
                               if len(agent.current_tasks) > 0])
        
        if current_workload < self.agent_spawn_threshold:
            return None
        
        # Determine what type of agent to create based on task
        if hasattr(task, 'requires_human_interaction') and task.requires_human_interaction:
            # Don't auto-create human-interactive agents
            return None
        
        # Create a sub-agent for the task
        capabilities = getattr(task, 'required_capabilities', ["general_purpose"])
        return await self.create_sub_agent(f"Auto-Agent-{uuid.uuid4().hex[:8]}", capabilities)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all agents"""
        stats = {
            "total_agents": len(self.agents),
            "active_agents": len([a for a in self.agents.values() if a.is_active]),
            "agents_by_role": {},
            "agents_by_status": {},
            "boss_agent": None,
            "agents": {}
        }
        
        # Count agents by role type
        for role_type in AgentRoleType:
            count = len(self._get_agents_by_type(role_type))
            stats["agents_by_role"][role_type.value] = count
        
        # Count agents by status
        for status in AgentStatus:
            count = len([a for a in self.agents.values() if a.config.status == status])
            stats["agents_by_status"][status.value] = count
        
        # Boss agent info
        if self.boss_agent:
            stats["boss_agent"] = self.boss_agent.get_status()
        
        # Individual agent stats
        for agent_id, agent in self.agents.items():
            stats["agents"][agent_id] = agent.get_status()
        
        return stats
    
    def get_agents_by_role_type(self, role_type: AgentRoleType) -> List[Dict[str, Any]]:
        """Get agents of a specific role type with their status"""
        agents = self._get_agents_by_type(role_type)
        return [agent.get_status() for agent in agents]
    
    def get_human_paired_agents(self) -> List[Dict[str, Any]]:
        """Get all human-paired agents with pairing information"""
        paired_agents = self._get_agents_by_type(AgentRoleType.HUMAN_PAIRED)
        
        result = []
        for agent in paired_agents:
            status = agent.get_status()
            if isinstance(agent, HumanPairedAgent):
                status["pairing_details"] = {
                    "human_name": agent.human_pairing.human_name,
                    "collaboration_level": agent.human_pairing.collaboration_level,
                    "communication_frequency": agent.human_pairing.communication_frequency,
                    "contact_method": agent.human_pairing.contact_method
                }
            result.append(status)
        
        return result
    
    def get_human_shadow_agents(self) -> List[Dict[str, Any]]:
        """Get all human-shadow agents with representation information"""
        shadow_agents = self._get_agents_by_type(AgentRoleType.HUMAN_SHADOW)
        
        result = []
        for agent in shadow_agents:
            status = agent.get_status()
            status["shadow_details"] = {
                "represented_human_id": agent.config.represented_human_id,
                "represented_human_name": agent.config.represented_human_name,
                "shadow_permissions": agent.config.shadow_permissions
            }
            result.append(status)
        
        return result
    
    def get_hierarchy_view(self) -> Dict[str, Any]:
        """Get a hierarchical view of standalone agents"""
        boss_agents = self._get_agents_by_hierarchy(AgentHierarchyLevel.BOSS)
        sub_agents = self._get_agents_by_hierarchy(AgentHierarchyLevel.SUB_AGENT)
        
        hierarchy = {
            "boss_agents": [agent.get_status() for agent in boss_agents],
            "sub_agents": [agent.get_status() for agent in sub_agents],
            "hierarchy_relationships": []
        }
        
        # Build parent-child relationships
        for sub_agent in sub_agents:
            if sub_agent.config.parent_agent_id:
                hierarchy["hierarchy_relationships"].append({
                    "parent_id": sub_agent.config.parent_agent_id,
                    "child_id": sub_agent.config.id,
                    "child_name": sub_agent.config.name
                })
        
        return hierarchy
    
    async def scale_agents(self, target_standalone: int = None, target_paired: int = None, 
                          target_shadow: int = None):
        """Scale the number of agents of each type"""
        if target_standalone is not None:
            await self._scale_standalone_agents(target_standalone)
        
        if target_paired is not None:
            await self._scale_paired_agents(target_paired)
        
        if target_shadow is not None:
            await self._scale_shadow_agents(target_shadow)
    
    async def _scale_standalone_agents(self, target_count: int):
        """Scale standalone sub-agents (excluding boss)"""
        current_sub_agents = self._get_agents_by_hierarchy(AgentHierarchyLevel.SUB_AGENT)
        current_count = len(current_sub_agents)
        
        if target_count > current_count:
            # Create new sub-agents
            for i in range(target_count - current_count):
                await self.create_sub_agent(f"Sub-Agent-{uuid.uuid4().hex[:8]}")
        elif target_count < current_count:
            # Remove idle sub-agents
            idle_agents = [agent for agent in current_sub_agents 
                          if agent.config.status == AgentStatus.IDLE and len(agent.current_tasks) == 0]
            
            agents_to_remove = min(len(idle_agents), current_count - target_count)
            for i in range(agents_to_remove):
                agent = idle_agents[i]
                await self._remove_agent(agent.config.id)
        
        logger.info(f"Scaled standalone sub-agents to target: {target_count}")
    
    async def _scale_paired_agents(self, target_count: int):
        """Scale human-paired agents (requires manual pairing)"""
        current_count = len(self._get_agents_by_type(AgentRoleType.HUMAN_PAIRED))
        logger.info(f"Current paired agents: {current_count}, target: {target_count}")
        
        if target_count < current_count:
            # Can only scale down by removing idle agents
            paired_agents = self._get_agents_by_type(AgentRoleType.HUMAN_PAIRED)
            idle_agents = [agent for agent in paired_agents 
                          if agent.config.status == AgentStatus.IDLE and len(agent.current_tasks) == 0]
            
            agents_to_remove = min(len(idle_agents), current_count - target_count)
            for i in range(agents_to_remove):
                await self._remove_agent(idle_agents[i].config.id)
    
    async def _scale_shadow_agents(self, target_count: int):
        """Scale human-shadow agents (requires manual shadow setup)"""
        current_count = len(self._get_agents_by_type(AgentRoleType.HUMAN_SHADOW))
        logger.info(f"Current shadow agents: {current_count}, target: {target_count}")
        
        if target_count < current_count:
            # Can only scale down by removing idle agents
            shadow_agents = self._get_agents_by_type(AgentRoleType.HUMAN_SHADOW)
            idle_agents = [agent for agent in shadow_agents 
                          if agent.config.status == AgentStatus.IDLE and len(agent.current_tasks) == 0]
            
            agents_to_remove = min(len(idle_agents), current_count - target_count)
            for i in range(agents_to_remove):
                await self._remove_agent(idle_agents[i].config.id)
    
    async def _remove_agent(self, agent_id: str):
        """Remove an agent from the system"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.stop()
            del self.agents[agent_id]
            logger.info(f"Removed agent: {agent.config.name}")
    
    def stop_all_agents(self):
        """Stop all agents"""
        logger.info("Stopping all role-based agents...")
        
        for agent in self.agents.values():
            agent.stop()
        
        logger.info("All role-based agents stopped")
    
    def remove_idle_agents(self, idle_timeout: int = 1800):
        """Remove agents that have been idle for too long"""
        current_time = datetime.utcnow()
        agents_to_remove = []
        
        for agent_id, agent in self.agents.items():
            # Don't remove boss agents or human-interactive agents automatically
            if (agent.config.role_type == AgentRoleType.STANDALONE_AGENT and
                agent.config.hierarchy_level == AgentHierarchyLevel.SUB_AGENT and
                agent.config.status == AgentStatus.IDLE and
                len(agent.current_tasks) == 0 and
                (current_time - agent.last_active).total_seconds() > idle_timeout):
                agents_to_remove.append(agent_id)
        
        for agent_id in agents_to_remove:
            asyncio.create_task(self._remove_agent(agent_id))
        
        return len(agents_to_remove)
    
    async def update_agent_model(self, agent_id: str, model_name: str, provider: Optional[str] = None) -> bool:
        """Update an agent's model configuration"""
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        
        try:
            # Update agent configuration
            agent.config.model_name = model_name
            if provider:
                agent.config.llm_provider = provider
            
            # Reinitialize DSPY module if applicable
            if hasattr(agent, '_initialize_dspy_module'):
                agent._initialize_dspy_module()
            
            logger.info(f"Updated agent {agent_id} to use model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent model: {e}")
            return False
    
    def receive_human_response(self, agent_id: str, task_id: str, response: Dict[str, Any]):
        """Route human response to the appropriate agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if isinstance(agent, HumanPairedAgent):
                agent.receive_human_response(task_id, response)
                logger.info(f"Routed human response to paired agent {agent_id}")
            else:
                logger.warning(f"Agent {agent_id} is not a human-paired agent")
        else:
            logger.error(f"Agent {agent_id} not found for human response routing")