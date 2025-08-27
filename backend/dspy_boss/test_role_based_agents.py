"""
Test cases for the role-based agent system
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from .models import (
    AgentConfig, AgentRoleType, AgentHierarchyLevel, AgentStatus,
    TaskDefinition, TaskStatus, TaskPriority, HumanPairing, PromptSignature
)
from .role_based_agents import StandaloneAgent, HumanPairedAgent, HumanShadowAgent
from .role_based_agent_manager import RoleBasedAgentManager


class TestRoleBasedAgents:
    """Test cases for role-based agent classes"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.task_manager = Mock()
        self.mcp_manager = Mock()
        self.prompt_signatures = {
            "boss_agent": PromptSignature(
                name="boss_agent",
                signature="task_description -> result, reasoning, delegation_recommendations"
            ),
            "sub_agent": PromptSignature(
                name="sub_agent", 
                signature="task_description -> result, reasoning"
            ),
            "human_paired": PromptSignature(
                name="human_paired",
                signature="task_description, human_context -> result, reasoning"
            ),
            "human_shadow": PromptSignature(
                name="human_shadow",
                signature="task_description, represented_human -> result, reasoning"
            )
        }
    
    def test_standalone_boss_agent_creation(self):
        """Test creating a standalone boss agent"""
        config = AgentConfig(
            name="Test Boss",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.BOSS,
            capabilities=["strategic_planning", "decision_making"],
            model_name="gpt-4",
            prompt_signature="boss_agent"
        )
        
        agent = StandaloneAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
        
        assert agent.config.name == "Test Boss"
        assert agent.config.role_type == AgentRoleType.STANDALONE_AGENT
        assert agent.config.hierarchy_level == AgentHierarchyLevel.BOSS
        assert "strategic_planning" in agent.config.capabilities
    
    def test_standalone_sub_agent_creation(self):
        """Test creating a standalone sub-agent"""
        config = AgentConfig(
            name="Test Sub-Agent",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            parent_agent_id="boss-123",
            capabilities=["data_processing", "analysis"],
            model_name="gpt-3.5-turbo",
            prompt_signature="sub_agent"
        )
        
        agent = StandaloneAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
        
        assert agent.config.hierarchy_level == AgentHierarchyLevel.SUB_AGENT
        assert agent.config.parent_agent_id == "boss-123"
        assert "data_processing" in agent.config.capabilities
    
    def test_human_paired_agent_creation(self):
        """Test creating a human-paired agent"""
        human_pairing = HumanPairing(
            human_id="human-123",
            human_name="John Doe",
            contact_method="slack",
            contact_details={"channel": "#ai-collaboration"},
            collaboration_level="standard"
        )
        
        config = AgentConfig(
            name="Collaborative Agent",
            role_type=AgentRoleType.HUMAN_PAIRED,
            human_pairing=human_pairing,
            capabilities=["collaboration", "communication"],
            model_name="gpt-4",
            prompt_signature="human_paired"
        )
        
        agent = HumanPairedAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
        
        assert agent.config.role_type == AgentRoleType.HUMAN_PAIRED
        assert agent.human_pairing.human_name == "John Doe"
        assert agent.human_pairing.collaboration_level == "standard"
    
    def test_human_shadow_agent_creation(self):
        """Test creating a human shadow agent"""
        config = AgentConfig(
            name="Shadow Agent",
            role_type=AgentRoleType.HUMAN_SHADOW,
            represented_human_id="human-456",
            represented_human_name="Jane Smith",
            shadow_permissions=["approve_purchases", "schedule_meetings", "respond_to_emails"],
            capabilities=["decision_making", "human_representation"],
            model_name="gpt-4",
            prompt_signature="human_shadow"
        )
        
        agent = HumanShadowAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
        
        assert agent.config.role_type == AgentRoleType.HUMAN_SHADOW
        assert agent.config.represented_human_name == "Jane Smith"
        assert "approve_purchases" in agent.config.shadow_permissions
    
    def test_standalone_agent_missing_hierarchy_level(self):
        """Test that standalone agents require hierarchy level"""
        config = AgentConfig(
            name="Invalid Agent",
            role_type=AgentRoleType.STANDALONE_AGENT,
            # Missing hierarchy_level
            capabilities=["general"]
        )
        
        with pytest.raises(ValueError, match="Standalone agents must have hierarchy_level specified"):
            StandaloneAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
    
    def test_human_paired_agent_missing_pairing(self):
        """Test that human-paired agents require pairing configuration"""
        config = AgentConfig(
            name="Invalid Paired Agent",
            role_type=AgentRoleType.HUMAN_PAIRED,
            # Missing human_pairing
            capabilities=["collaboration"]
        )
        
        with pytest.raises(ValueError, match="Human-paired agents must have human_pairing configuration"):
            HumanPairedAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)
    
    def test_human_shadow_agent_missing_representation(self):
        """Test that human shadow agents require representation info"""
        config = AgentConfig(
            name="Invalid Shadow Agent",
            role_type=AgentRoleType.HUMAN_SHADOW,
            # Missing represented_human_id and represented_human_name
            capabilities=["decision_making"]
        )
        
        with pytest.raises(ValueError, match="Human-shadow agents must have represented_human_id and represented_human_name"):
            HumanShadowAgent(config, self.task_manager, self.mcp_manager, self.prompt_signatures)


class TestRoleBasedAgentManager:
    """Test cases for role-based agent manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.task_manager = Mock()
        self.mcp_manager = Mock()
        self.manager = RoleBasedAgentManager(self.task_manager, self.mcp_manager)
        
        self.prompt_signatures = {
            "boss_agent": PromptSignature(
                name="boss_agent",
                signature="task_description -> result, reasoning"
            ),
            "sub_agent": PromptSignature(
                name="sub_agent",
                signature="task_description -> result, reasoning"
            )
        }
    
    @pytest.mark.asyncio
    async def test_create_boss_agent(self):
        """Test creating a boss agent"""
        boss_agent = await self.manager.create_boss_agent("Test Boss")
        
        assert boss_agent is not None
        assert boss_agent.config.name == "Test Boss"
        assert boss_agent.config.hierarchy_level == AgentHierarchyLevel.BOSS
        assert self.manager.boss_agent == boss_agent
    
    @pytest.mark.asyncio
    async def test_create_sub_agent(self):
        """Test creating a sub-agent"""
        # First create boss agent
        boss_agent = await self.manager.create_boss_agent("Boss")
        
        sub_agent = await self.manager.create_sub_agent("Sub Agent", ["data_processing"])
        
        assert sub_agent is not None
        assert sub_agent.config.name == "Sub Agent"
        assert sub_agent.config.hierarchy_level == AgentHierarchyLevel.SUB_AGENT
        assert sub_agent.config.parent_agent_id == boss_agent.config.id
    
    @pytest.mark.asyncio
    async def test_create_human_paired_agent(self):
        """Test creating a human-paired agent"""
        human_pairing = HumanPairing(
            human_id="human-123",
            human_name="Test Human",
            contact_method="slack",
            contact_details={"channel": "#test"}
        )
        
        paired_agent = await self.manager.create_human_paired_agent(
            "Paired Agent", human_pairing, ["collaboration"]
        )
        
        assert paired_agent is not None
        assert paired_agent.config.name == "Paired Agent"
        assert paired_agent.config.role_type == AgentRoleType.HUMAN_PAIRED
        assert paired_agent.human_pairing.human_name == "Test Human"
    
    @pytest.mark.asyncio
    async def test_create_human_shadow_agent(self):
        """Test creating a human shadow agent"""
        shadow_agent = await self.manager.create_human_shadow_agent(
            "Shadow Agent",
            "human-456",
            "Shadow Human",
            ["approve_tasks", "make_decisions"],
            ["decision_making"]
        )
        
        assert shadow_agent is not None
        assert shadow_agent.config.name == "Shadow Agent"
        assert shadow_agent.config.role_type == AgentRoleType.HUMAN_SHADOW
        assert shadow_agent.config.represented_human_name == "Shadow Human"
        assert "approve_tasks" in shadow_agent.config.shadow_permissions
    
    def test_get_agents_by_role_type(self):
        """Test filtering agents by role type"""
        # Create mock agents
        standalone_config = AgentConfig(
            name="Standalone", 
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT
        )
        paired_config = AgentConfig(
            name="Paired",
            role_type=AgentRoleType.HUMAN_PAIRED,
            human_pairing=HumanPairing(
                human_id="test", human_name="Test", contact_method="slack"
            )
        )
        
        # Add to manager (mocking the creation process)
        self.manager.agents["standalone"] = Mock()
        self.manager.agents["standalone"].config = standalone_config
        self.manager.agents["paired"] = Mock() 
        self.manager.agents["paired"].config = paired_config
        
        standalone_agents = self.manager._get_agents_by_type(AgentRoleType.STANDALONE_AGENT)
        paired_agents = self.manager._get_agents_by_type(AgentRoleType.HUMAN_PAIRED)
        
        assert len(standalone_agents) == 1
        assert len(paired_agents) == 1
        assert standalone_agents[0].config.name == "Standalone"
        assert paired_agents[0].config.name == "Paired"
    
    def test_get_hierarchy_view(self):
        """Test getting hierarchical view of agents"""
        # Create mock boss and sub-agents
        boss_config = AgentConfig(
            name="Boss",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.BOSS
        )
        sub_config = AgentConfig(
            name="Sub",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            parent_agent_id="boss-id"
        )
        
        boss_agent = Mock()
        boss_agent.config = boss_config
        boss_agent.get_status.return_value = {"id": "boss-id", "name": "Boss"}
        
        sub_agent = Mock()
        sub_agent.config = sub_config
        sub_agent.get_status.return_value = {"id": "sub-id", "name": "Sub"}
        
        self.manager.agents["boss"] = boss_agent
        self.manager.agents["sub"] = sub_agent
        
        hierarchy = self.manager.get_hierarchy_view()
        
        assert len(hierarchy["boss_agents"]) == 1
        assert len(hierarchy["sub_agents"]) == 1
        assert len(hierarchy["hierarchy_relationships"]) == 1
        assert hierarchy["hierarchy_relationships"][0]["parent_id"] == "boss-id"
        assert hierarchy["hierarchy_relationships"][0]["child_id"] == "sub-id"


class TestTaskAssignment:
    """Test cases for task assignment in role-based system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.task_manager = Mock()
        self.mcp_manager = Mock()
        self.manager = RoleBasedAgentManager(self.task_manager, self.mcp_manager)
    
    @pytest.mark.asyncio
    async def test_task_assignment_to_suitable_agent(self):
        """Test task assignment to most suitable agent"""
        # Create a mock task
        task = TaskDefinition(
            name="Test Task",
            description="A test task",
            function_name="test_function",
            required_capabilities=["data_processing"]
        )
        
        # Create mock agents with different suitability
        good_agent = Mock()
        good_agent.config = AgentConfig(
            name="Good Agent",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            capabilities=["data_processing", "analysis"],
            status=AgentStatus.IDLE
        )
        good_agent.can_accept_task = AsyncMock(return_value=True)
        good_agent.assign_task = AsyncMock(return_value=True)
        good_agent.current_tasks = []
        good_agent.config.total_tasks_completed = 10
        good_agent.config.performance_score = 0.9
        good_agent.config.max_concurrent_tasks = 3
        
        poor_agent = Mock()
        poor_agent.config = AgentConfig(
            name="Poor Agent",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            capabilities=["general"],  # Doesn't match required capability
            status=AgentStatus.IDLE
        )
        poor_agent.can_accept_task = AsyncMock(return_value=True)
        poor_agent.assign_task = AsyncMock(return_value=True)
        poor_agent.current_tasks = []
        poor_agent.config.total_tasks_completed = 2
        poor_agent.config.performance_score = 0.5
        poor_agent.config.max_concurrent_tasks = 3
        
        self.manager.agents["good"] = good_agent
        self.manager.agents["poor"] = poor_agent
        
        # Assign task
        assigned_agent = await self.manager.assign_task_to_best_agent(task)
        
        assert assigned_agent == good_agent
        good_agent.assign_task.assert_called_once_with(task)
    
    @pytest.mark.asyncio
    async def test_boss_agent_priority_for_strategic_tasks(self):
        """Test that boss agents get priority for strategic tasks"""
        # Create strategic task
        task = TaskDefinition(
            name="Strategic Decision",
            description="Make strategic decision",
            function_name="strategic_decision",
            requires_boss_level=True
        )
        
        # Create boss and sub-agent
        boss_agent = Mock()
        boss_agent.config = AgentConfig(
            name="Boss",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.BOSS,
            status=AgentStatus.IDLE
        )
        boss_agent.can_accept_task = AsyncMock(return_value=True)
        boss_agent.assign_task = AsyncMock(return_value=True)
        boss_agent.current_tasks = []
        boss_agent.config.performance_score = 0.8
        boss_agent.config.max_concurrent_tasks = 5
        
        sub_agent = Mock()
        sub_agent.config = AgentConfig(
            name="Sub",
            role_type=AgentRoleType.STANDALONE_AGENT,
            hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
            status=AgentStatus.IDLE
        )
        sub_agent.can_accept_task = AsyncMock(return_value=True)
        sub_agent.assign_task = AsyncMock(return_value=True)
        sub_agent.current_tasks = []
        sub_agent.config.performance_score = 0.9  # Higher performance but not boss
        sub_agent.config.max_concurrent_tasks = 3
        
        self.manager.agents["boss"] = boss_agent
        self.manager.agents["sub"] = sub_agent
        
        # Assign task
        assigned_agent = await self.manager.assign_task_to_best_agent(task)
        
        assert assigned_agent == boss_agent
        boss_agent.assign_task.assert_called_once_with(task)


def test_backward_compatibility():
    """Test that the new system maintains backward compatibility"""
    # Test old AgentType still works
    old_config = AgentConfig(
        name="Legacy Agent",
        type=AgentType.AGENTIC,  # Using old type system
        capabilities=["general"]
    )
    
    # Should be able to access through new property
    assert old_config.role_type == AgentType.AGENTIC
    assert old_config.type == AgentType.AGENTIC


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])