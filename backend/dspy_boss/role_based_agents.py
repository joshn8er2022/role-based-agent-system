"""
Role-based agent system for DSPY Boss
Supports Human-Paired, Human-Shadow, and Standalone agents
"""

import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import uuid
from abc import ABC, abstractmethod

import dspy
from dspy import Signature, InputField, OutputField

from .models import (
    AgentConfig, AgentRoleType, AgentHierarchyLevel, AgentStatus, 
    TaskDefinition, TaskStatus, PromptSignature, HumanPairing
)
from .task_manager import TaskManager
from .mcp import MCPManager


class BaseRoleAgent(ABC):
    """Abstract base class for all role-based agents"""
    
    def __init__(self, config: AgentConfig, task_manager: TaskManager, mcp_manager: MCPManager):
        self.config = config
        self.task_manager = task_manager
        self.mcp_manager = mcp_manager
        
        self.is_active = False
        self.current_tasks: List[str] = []
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Performance metrics
        self.last_active = datetime.utcnow()
        
        logger.info(f"Initialized {self.config.role_type.value} agent: {self.config.name}")
    
    @abstractmethod
    async def execute_task(self, task: TaskDefinition) -> Any:
        """Execute a task (to be implemented by subclasses)"""
        pass
    
    @abstractmethod
    async def can_accept_task(self, task: TaskDefinition) -> bool:
        """Check if agent can accept a new task"""
        pass
    
    def start(self):
        """Start the agent in a separate thread"""
        if self.is_active:
            return
        
        self.is_active = True
        self.config.status = AgentStatus.ACTIVE
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"Started agent: {self.config.name}")
    
    def stop(self):
        """Stop the agent"""
        if not self.is_active:
            return
        
        self.is_active = False
        self.config.status = AgentStatus.OFFLINE
        self.stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Stopped agent: {self.config.name}")
    
    def _run_loop(self):
        """Main execution loop for the agent"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        
        try:
            loop.run_until_complete(self._async_run_loop())
        except Exception as e:
            logger.error(f"Error in agent {self.config.name} run loop: {e}")
        finally:
            loop.close()
    
    async def _async_run_loop(self):
        """Async run loop"""
        while self.is_active and not self.stop_event.is_set():
            try:
                # Check for assigned tasks
                if self.current_tasks:
                    task_id = self.current_tasks[0]  # Process first task
                    task = self.task_manager.get_task_status(task_id)
                    
                    if task and task.status == TaskStatus.PENDING:
                        await self._process_task(task)
                
                await asyncio.sleep(1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Error in agent {self.config.name} async loop: {e}")
                await asyncio.sleep(5)  # Longer delay on error
    
    async def _process_task(self, task: TaskDefinition):
        """Process a single task"""
        start_time = datetime.utcnow()
        
        try:
            self.config.status = AgentStatus.BUSY
            task.status = TaskStatus.RUNNING
            task.started_at = start_time
            
            # Execute the task
            result = await self.execute_task(task)
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
            # Update metrics
            duration = (task.completed_at - start_time).total_seconds()
            self._update_metrics(True, duration)
            
            # Move task to completed
            self.current_tasks.remove(task.id)
            self.completed_tasks.append(task.id)
            
            self.config.status = AgentStatus.IDLE
            logger.info(f"Agent {self.config.name} completed task: {task.name}")
            
        except Exception as e:
            # Task failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(False, duration)
            
            # Move task to failed
            self.current_tasks.remove(task.id)
            self.failed_tasks.append(task.id)
            
            self.config.status = AgentStatus.ERROR
            logger.error(f"Agent {self.config.name} failed task {task.name}: {e}")
    
    def _update_metrics(self, success: bool, duration: float):
        """Update performance metrics"""
        self.config.total_tasks_completed += 1
        
        # Update success rate
        successful_tasks = len(self.completed_tasks)
        self.config.success_rate = (successful_tasks / self.config.total_tasks_completed) * 100
        
        # Update average response time
        total_duration = self.config.average_response_time * (self.config.total_tasks_completed - 1) + duration
        self.config.average_response_time = total_duration / self.config.total_tasks_completed
        
        # Update performance score based on recent performance
        if self.config.total_tasks_completed >= 5:  # Only after some tasks
            recent_success_weight = 0.7
            historical_weight = 0.3
            current_success = 1.0 if success else 0.0
            
            self.config.performance_score = (
                recent_success_weight * current_success + 
                historical_weight * (self.config.success_rate / 100.0)
            )
    
    async def assign_task(self, task: TaskDefinition) -> bool:
        """Assign a task to this agent"""
        if not await self.can_accept_task(task):
            return False
        
        self.current_tasks.append(task.id)
        task.assigned_agent_id = self.config.id
        self.last_active = datetime.utcnow()
        
        logger.info(f"Assigned task {task.name} to agent {self.config.name}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "id": self.config.id,
            "name": self.config.name,
            "role_type": self.config.role_type.value,
            "hierarchy_level": self.config.hierarchy_level.value if self.config.hierarchy_level else None,
            "status": self.config.status.value,
            "is_active": self.is_active,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "total_tasks_completed": self.config.total_tasks_completed,
            "success_rate": round(self.config.success_rate, 2),
            "performance_score": round(self.config.performance_score, 2),
            "average_response_time": round(self.config.average_response_time, 2),
            "last_active": self.last_active.isoformat(),
            "capabilities": self.config.capabilities,
            "human_pairing": self.config.human_pairing.model_dump() if self.config.human_pairing else None,
            "represented_human": self.config.represented_human_name if self.config.represented_human_name else None
        }


class StandaloneAgent(BaseRoleAgent):
    """Standalone agent that can be either a boss or sub-agent"""
    
    def __init__(self, config: AgentConfig, task_manager: TaskManager, mcp_manager: MCPManager, 
                 prompt_signatures: Dict[str, PromptSignature]):
        super().__init__(config, task_manager, mcp_manager)
        
        self.prompt_signatures = prompt_signatures
        self.dspy_module = None
        
        # Validate configuration
        if config.hierarchy_level is None:
            raise ValueError("Standalone agents must have hierarchy_level specified")
        
        # Initialize DSPY module
        self._initialize_dspy_module()
    
    def _initialize_dspy_module(self):
        """Initialize DSPY module based on configuration"""
        try:
            # Get prompt signature
            signature_name = self.config.prompt_signature
            if signature_name and signature_name in self.prompt_signatures:
                prompt_sig = self.prompt_signatures[signature_name]
                
                if prompt_sig.is_react_agent:
                    self.dspy_module = dspy.ReAct(ReactAgentSignature)
                else:
                    self.dspy_module = dspy.ChainOfThought(StandaloneAgentSignature)
            else:
                # Default based on hierarchy level
                if self.config.hierarchy_level == AgentHierarchyLevel.BOSS:
                    self.dspy_module = dspy.ChainOfThought(BossAgentSignature)
                else:
                    self.dspy_module = dspy.ChainOfThought(StandaloneAgentSignature)
            
            logger.info(f"Initialized DSPY module for standalone agent {self.config.name}")
            
        except Exception as e:
            logger.error(f"Error initializing DSPY module for agent {self.config.name}: {e}")
            self.dspy_module = dspy.ChainOfThought(StandaloneAgentSignature)
    
    async def can_accept_task(self, task: TaskDefinition) -> bool:
        """Check if agent can accept a new task"""
        if not self.config.is_available:
            return False
        
        if len(self.current_tasks) >= self.config.max_concurrent_tasks:
            return False
        
        # Boss agents can handle any task, sub-agents need capability matching
        if self.config.hierarchy_level == AgentHierarchyLevel.BOSS:
            return True
        
        # Check if agent has required capabilities
        if hasattr(task, 'required_capabilities'):
            for capability in task.required_capabilities:
                if capability not in self.config.capabilities:
                    return False
        
        return True
    
    async def execute_task(self, task: TaskDefinition) -> Any:
        """Execute task using DSPY"""
        if not self.dspy_module:
            raise RuntimeError("DSPY module not initialized")
        
        try:
            # Prepare context
            context = {
                "task_id": task.id,
                "parameters": task.parameters,
                "capabilities": self.config.capabilities,
                "hierarchy_level": self.config.hierarchy_level.value,
                "parent_agent": self.config.parent_agent_id,
                "available_mcp_servers": self.mcp_manager.get_connected_servers()
            }
            
            # Execute DSPY module
            if isinstance(self.dspy_module, dspy.ReAct):
                result = await self._execute_react_agent(task, context)
            else:
                result = await self._execute_chain_of_thought(task, context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing task with DSPY: {e}")
            raise
    
    async def _execute_chain_of_thought(self, task: TaskDefinition, context: Dict[str, Any]) -> Any:
        """Execute using ChainOfThought"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    lambda: self.dspy_module(
                        task_description=task.description,
                        context=str(context),
                        agent_role=self.config.hierarchy_level.value
                    )
                )
            
            return {
                "result": result.result,
                "reasoning": result.reasoning,
                "method": "chain_of_thought",
                "agent_type": "standalone",
                "hierarchy_level": self.config.hierarchy_level.value
            }
            
        except Exception as e:
            logger.error(f"Error in ChainOfThought execution: {e}")
            raise
    
    async def _execute_react_agent(self, task: TaskDefinition, context: Dict[str, Any]) -> Any:
        """Execute using ReAct agent"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    lambda: self.dspy_module(
                        question=task.description,
                        context=str(context)
                    )
                )
            
            return {
                "answer": result.answer,
                "thought": result.thought,
                "action": result.action,
                "observation": result.observation,
                "method": "react",
                "agent_type": "standalone",
                "hierarchy_level": self.config.hierarchy_level.value
            }
            
        except Exception as e:
            logger.error(f"Error in ReAct execution: {e}")
            raise


class HumanPairedAgent(BaseRoleAgent):
    """Agent that works in collaboration with a human"""
    
    def __init__(self, config: AgentConfig, task_manager: TaskManager, mcp_manager: MCPManager,
                 prompt_signatures: Dict[str, PromptSignature]):
        super().__init__(config, task_manager, mcp_manager)
        
        self.prompt_signatures = prompt_signatures
        self.dspy_module = None
        
        # Validate configuration
        if config.human_pairing is None:
            raise ValueError("Human-paired agents must have human_pairing configuration")
        
        self.human_pairing = config.human_pairing
        self.pending_human_responses: Dict[str, TaskDefinition] = {}
        
        # Initialize DSPY module for collaborative tasks
        self._initialize_dspy_module()
    
    def _initialize_dspy_module(self):
        """Initialize DSPY module for collaborative tasks"""
        try:
            self.dspy_module = dspy.ChainOfThought(HumanPairedSignature)
            logger.info(f"Initialized DSPY module for human-paired agent {self.config.name}")
        except Exception as e:
            logger.error(f"Error initializing DSPY module for agent {self.config.name}: {e}")
            self.dspy_module = dspy.ChainOfThought(HumanPairedSignature)
    
    async def can_accept_task(self, task: TaskDefinition) -> bool:
        """Check if agent can accept a new task"""
        if not self.config.is_available:
            return False
        
        if len(self.current_tasks) >= self.config.max_concurrent_tasks:
            return False
        
        # Check collaboration level requirements
        if hasattr(task, 'requires_intensive_collaboration'):
            if (task.requires_intensive_collaboration and 
                self.human_pairing.collaboration_level != "intensive"):
                return False
        
        return True
    
    async def execute_task(self, task: TaskDefinition) -> Any:
        """Execute task in collaboration with human"""
        try:
            # Analyze if task requires human input
            analysis = await self._analyze_task_requirements(task)
            
            if analysis["requires_human_input"]:
                # Get human input first
                human_input = await self._get_human_input(task, analysis["human_input_type"])
                
                # Proceed with AI processing incorporating human input
                result = await self._execute_collaborative_task(task, human_input)
            else:
                # Can handle autonomously but notify human
                result = await self._execute_autonomous_task(task)
                await self._notify_human_of_completion(task, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing collaborative task: {e}")
            raise
    
    async def _analyze_task_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Analyze if task requires human input"""
        try:
            analysis_prompt = f"""
            Analyze this task to determine if human input is required:
            
            Task: {task.description}
            Parameters: {task.parameters}
            Collaboration Level: {self.human_pairing.collaboration_level}
            
            Determine:
            1. Does this require human input/decision-making?
            2. What type of human input? (approval, creative_input, domain_expertise, decision_making)
            3. Can it be handled autonomously?
            """
            
            # Use DSPY to analyze
            result = self.dspy_module(
                task_description=analysis_prompt,
                human_context=f"Paired with {self.human_pairing.human_name}",
                collaboration_level=self.human_pairing.collaboration_level
            )
            
            # Parse result (simplified - in production would use structured output)
            requires_human = "requires human" in result.result.lower()
            
            return {
                "requires_human_input": requires_human,
                "human_input_type": "approval" if requires_human else None,
                "analysis": result.result,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            logger.error(f"Error analyzing task requirements: {e}")
            return {"requires_human_input": False, "human_input_type": None}
    
    async def _get_human_input(self, task: TaskDefinition, input_type: str) -> Dict[str, Any]:
        """Get input from paired human"""
        try:
            # Format request message
            message = self._format_collaboration_request(task, input_type)
            
            # Send to human via configured contact method
            await self._send_collaboration_message(message, task.id)
            
            # Wait for response
            response = await self._wait_for_human_response(task.id)
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting human input: {e}")
            raise
    
    def _format_collaboration_request(self, task: TaskDefinition, input_type: str) -> str:
        """Format collaboration request message"""
        return f"""
🤝 **Collaboration Request from {self.config.name}**

**Task:** {task.name}
**Description:** {task.description}
**Input Needed:** {input_type}

**Your paired AI agent needs your input to proceed with this task.**

Please respond with:
- ✅ Approved: [any comments]
- 🔄 Modify: [specific changes needed]
- ❌ Reject: [reason for rejection]
- 💡 Input: [your creative input/expertise]

**Task ID:** {task.id}
**Collaboration Level:** {self.human_pairing.collaboration_level}
        """.strip()
    
    async def _send_collaboration_message(self, message: str, task_id: str):
        """Send collaboration message to human"""
        contact_method = self.human_pairing.contact_method
        contact_details = self.human_pairing.contact_details
        
        if contact_method == "slack":
            await self._send_slack_message(message, contact_details)
        elif contact_method == "close_crm":
            await self._send_crm_message(message, contact_details)
        else:
            logger.warning(f"Unsupported contact method for collaboration: {contact_method}")
    
    async def _send_slack_message(self, message: str, contact_details: Dict[str, Any]):
        """Send message via Slack"""
        # Implementation similar to original HumanAgent but for collaboration
        slack_servers = self.mcp_manager.find_servers_by_capability("messaging")
        
        if not slack_servers:
            raise RuntimeError("No Slack MCP server available")
        
        server_name = slack_servers[0]
        
        data = {
            "channel": contact_details.get("channel", "#general"),
            "text": message,
            "username": f"{self.config.name} (AI Collaborator)"
        }
        
        response = await self.mcp_manager.send_request(server_name, "POST", "chat.postMessage", data)
        
        if not response.success:
            raise RuntimeError(f"Failed to send Slack collaboration message: {response.error}")
    
    async def _send_crm_message(self, message: str, contact_details: Dict[str, Any]):
        """Send message via CRM"""
        crm_servers = self.mcp_manager.find_servers_by_capability("crm")
        
        if not crm_servers:
            raise RuntimeError("No CRM MCP server available")
        
        server_name = crm_servers[0]
        
        data = {
            "user_id": contact_details.get("user_id"),
            "message": message,
            "subject": f"Collaboration Request from {self.config.name}"
        }
        
        response = await self.mcp_manager.send_request(server_name, "POST", "messages", data)
        
        if not response.success:
            raise RuntimeError(f"Failed to send CRM collaboration message: {response.error}")
    
    async def _wait_for_human_response(self, task_id: str, timeout: int = 3600) -> Dict[str, Any]:
        """Wait for human response to collaboration request"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            # Check if response received
            if task_id in self.pending_human_responses:
                response = self.pending_human_responses.pop(task_id)
                return response
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        raise TimeoutError(f"Human {self.human_pairing.human_name} did not respond within {timeout} seconds")
    
    async def _execute_collaborative_task(self, task: TaskDefinition, human_input: Dict[str, Any]) -> Any:
        """Execute task with human input"""
        try:
            context = {
                "task_id": task.id,
                "parameters": task.parameters,
                "human_input": human_input,
                "human_name": self.human_pairing.human_name,
                "collaboration_level": self.human_pairing.collaboration_level
            }
            
            result = self.dspy_module(
                task_description=task.description,
                human_context=str(human_input),
                collaboration_level=self.human_pairing.collaboration_level
            )
            
            return {
                "result": result.result,
                "reasoning": result.reasoning,
                "method": "collaborative",
                "agent_type": "human_paired",
                "human_input": human_input,
                "collaboration_level": self.human_pairing.collaboration_level
            }
            
        except Exception as e:
            logger.error(f"Error in collaborative task execution: {e}")
            raise
    
    async def _execute_autonomous_task(self, task: TaskDefinition) -> Any:
        """Execute task autonomously but with human notification"""
        try:
            result = self.dspy_module(
                task_description=task.description,
                human_context=f"Autonomous execution (will notify {self.human_pairing.human_name})",
                collaboration_level=self.human_pairing.collaboration_level
            )
            
            return {
                "result": result.result,
                "reasoning": result.reasoning,
                "method": "autonomous_with_notification",
                "agent_type": "human_paired",
                "human_notified": True
            }
            
        except Exception as e:
            logger.error(f"Error in autonomous task execution: {e}")
            raise
    
    async def _notify_human_of_completion(self, task: TaskDefinition, result: Any):
        """Notify human of task completion"""
        message = f"""
✅ **Task Completed by {self.config.name}**

**Task:** {task.name}
**Result:** {result.get('result', 'N/A')}
**Method:** {result.get('method', 'N/A')}

Your paired AI agent has completed this task autonomously.
        """.strip()
        
        await self._send_collaboration_message(message, task.id)
    
    def receive_human_response(self, task_id: str, response: Dict[str, Any]):
        """Receive response from human collaborator"""
        self.pending_human_responses[task_id] = response
        logger.info(f"Received collaboration response for task {task_id} from {self.human_pairing.human_name}")


class HumanShadowAgent(BaseRoleAgent):
    """Agent that acts as a shadow/representative of a human"""
    
    def __init__(self, config: AgentConfig, task_manager: TaskManager, mcp_manager: MCPManager,
                 prompt_signatures: Dict[str, PromptSignature]):
        super().__init__(config, task_manager, mcp_manager)
        
        self.prompt_signatures = prompt_signatures
        self.dspy_module = None
        
        # Validate configuration
        if not config.represented_human_id or not config.represented_human_name:
            raise ValueError("Human-shadow agents must have represented_human_id and represented_human_name")
        
        # Initialize DSPY module for shadow operations
        self._initialize_dspy_module()
    
    def _initialize_dspy_module(self):
        """Initialize DSPY module for shadow operations"""
        try:
            self.dspy_module = dspy.ChainOfThought(HumanShadowSignature)
            logger.info(f"Initialized DSPY module for human-shadow agent {self.config.name}")
        except Exception as e:
            logger.error(f"Error initializing DSPY module for agent {self.config.name}: {e}")
            self.dspy_module = dspy.ChainOfThought(HumanShadowSignature)
    
    async def can_accept_task(self, task: TaskDefinition) -> bool:
        """Check if shadow agent can accept a task"""
        if not self.config.is_available:
            return False
        
        if len(self.current_tasks) >= self.config.max_concurrent_tasks:
            return False
        
        # Check if task is within shadow permissions
        if hasattr(task, 'required_permissions'):
            for permission in task.required_permissions:
                if permission not in self.config.shadow_permissions:
                    return False
        
        return True
    
    async def execute_task(self, task: TaskDefinition) -> Any:
        """Execute task as human representative"""
        try:
            # Check if task requires human-like decision making
            decision_analysis = await self._analyze_human_decision_requirements(task)
            
            if decision_analysis["requires_human_consultation"]:
                # This task requires actual human input - escalate
                return await self._escalate_to_human(task)
            else:
                # Can act as human shadow
                return await self._execute_as_human_shadow(task)
            
        except Exception as e:
            logger.error(f"Error executing shadow task: {e}")
            raise
    
    async def _analyze_human_decision_requirements(self, task: TaskDefinition) -> Dict[str, Any]:
        """Analyze if task requires actual human consultation"""
        try:
            analysis_prompt = f"""
            As a shadow agent representing {self.config.represented_human_name}, 
            analyze if this task requires actual human consultation or if I can handle it
            as their representative.
            
            Task: {task.description}
            Parameters: {task.parameters}
            My Permissions: {self.config.shadow_permissions}
            
            Consider:
            1. Is this within my permissions?
            2. Would the human want to make this decision personally?
            3. Are there ethical/legal implications?
            4. Is this routine enough for shadow handling?
            """
            
            result = self.dspy_module(
                task_description=analysis_prompt,
                represented_human=self.config.represented_human_name,
                shadow_permissions=", ".join(self.config.shadow_permissions)
            )
            
            requires_consultation = "requires consultation" in result.result.lower()
            
            return {
                "requires_human_consultation": requires_consultation,
                "analysis": result.result,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            logger.error(f"Error analyzing human decision requirements: {e}")
            return {"requires_human_consultation": True}  # Err on side of caution
    
    async def _execute_as_human_shadow(self, task: TaskDefinition) -> Any:
        """Execute task as human shadow"""
        try:
            # Simulate human decision-making patterns
            context = {
                "task_id": task.id,
                "parameters": task.parameters,
                "represented_human": self.config.represented_human_name,
                "shadow_permissions": self.config.shadow_permissions
            }
            
            result = self.dspy_module(
                task_description=task.description,
                represented_human=self.config.represented_human_name,
                shadow_permissions=", ".join(self.config.shadow_permissions)
            )
            
            return {
                "result": result.result,
                "reasoning": result.reasoning,
                "method": "human_shadow",
                "agent_type": "human_shadow",
                "represented_human": self.config.represented_human_name,
                "acted_with_permissions": self.config.shadow_permissions
            }
            
        except Exception as e:
            logger.error(f"Error in shadow execution: {e}")
            raise
    
    async def _escalate_to_human(self, task: TaskDefinition) -> Any:
        """Escalate task to actual human"""
        try:
            # Create escalation message
            message = f"""
🚨 **Task Escalation from Shadow Agent {self.config.name}**

**Task:** {task.name}
**Description:** {task.description}

**Reason for Escalation:**
This task requires your personal attention and cannot be handled by your shadow agent.

**Please handle this task directly or provide specific instructions.**

**Task ID:** {task.id}
            """.strip()
            
            # Send escalation via configured contact method
            if self.config.contact_method:
                await self._send_escalation_message(message, task)
            
            return {
                "result": "Task escalated to human",
                "method": "escalation",
                "agent_type": "human_shadow",
                "escalated_to": self.config.represented_human_name,
                "reason": "Requires human decision-making"
            }
            
        except Exception as e:
            logger.error(f"Error escalating task to human: {e}")
            raise
    
    async def _send_escalation_message(self, message: str, task: TaskDefinition):
        """Send escalation message to represented human"""
        # Similar to other communication methods but marked as escalation
        if self.config.contact_method == "slack":
            await self._send_slack_escalation(message, task)
        elif self.config.contact_method == "close_crm":
            await self._send_crm_escalation(message, task)
        else:
            logger.warning(f"No contact method configured for escalation")
    
    async def _send_slack_escalation(self, message: str, task: TaskDefinition):
        """Send escalation via Slack"""
        slack_servers = self.mcp_manager.find_servers_by_capability("messaging")
        
        if slack_servers:
            server_name = slack_servers[0]
            data = {
                "channel": self.config.contact_details.get("channel", "#general"),
                "text": message,
                "username": f"Shadow Agent - {self.config.name}"
            }
            
            await self.mcp_manager.send_request(server_name, "POST", "chat.postMessage", data)
    
    async def _send_crm_escalation(self, message: str, task: TaskDefinition):
        """Send escalation via CRM"""
        crm_servers = self.mcp_manager.find_servers_by_capability("crm")
        
        if crm_servers:
            server_name = crm_servers[0]
            data = {
                "user_id": self.config.contact_details.get("user_id"),
                "message": message,
                "subject": f"Task Escalation from Shadow Agent"
            }
            
            await self.mcp_manager.send_request(server_name, "POST", "messages", data)


# DSPY Signatures for different agent types

class StandaloneAgentSignature(Signature):
    """Signature for standalone agents"""
    task_description = InputField(desc="Task to be performed")
    context = InputField(desc="Available context and resources")
    agent_role = InputField(desc="Agent's role (boss or sub_agent)")
    
    result = OutputField(desc="Task execution result")
    reasoning = OutputField(desc="Reasoning behind the result")


class BossAgentSignature(Signature):
    """Signature for boss agents with strategic capabilities"""
    task_description = InputField(desc="Strategic task or decision to be made")
    context = InputField(desc="System state and available resources")
    agent_role = InputField(desc="Boss agent role")
    
    result = OutputField(desc="Strategic decision or task result")
    reasoning = OutputField(desc="Strategic reasoning and considerations")
    delegation_recommendations = OutputField(desc="Recommendations for task delegation")


class HumanPairedSignature(Signature):
    """Signature for human-paired collaborative agents"""
    task_description = InputField(desc="Collaborative task to be performed")
    human_context = InputField(desc="Human input or collaboration context")
    collaboration_level = InputField(desc="Level of collaboration required")
    
    result = OutputField(desc="Collaborative task result")
    reasoning = OutputField(desc="Reasoning incorporating human input")


class HumanShadowSignature(Signature):
    """Signature for human shadow agents"""
    task_description = InputField(desc="Task to be performed as human representative")
    represented_human = InputField(desc="Name of human being represented")
    shadow_permissions = InputField(desc="Permissions granted to shadow agent")
    
    result = OutputField(desc="Decision/action taken as human representative")
    reasoning = OutputField(desc="Human-like reasoning for the decision")


class ReactAgentSignature(Signature):
    """React agent signature for step-by-step reasoning"""
    question = InputField(desc="Question or task to solve")
    context = InputField(desc="Available context and tools")
    
    thought = OutputField(desc="Current thought process")
    action = OutputField(desc="Action to take")
    observation = OutputField(desc="Observation from the action")
    answer = OutputField(desc="Final answer or result")