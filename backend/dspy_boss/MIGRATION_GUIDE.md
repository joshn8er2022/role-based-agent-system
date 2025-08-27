# Migration Guide: Role-Based Agent System

This guide helps you migrate from the previous agent system to the new role-based agent system that supports three distinct agent types:

1. **Human-Paired Agents** - Collaborative agents that work directly with humans
2. **Human Shadow Agents** - Agents that act as representatives of humans in the background  
3. **Standalone Agents** - Independent agents (can be boss agents or sub-agents)

## Key Changes

### Agent Type System

**Before:**
```python
class AgentType(str, Enum):
    AGENTIC = "agentic"
    HUMAN = "human"
```

**After:**
```python
class AgentRoleType(str, Enum):
    HUMAN_PAIRED = "human_paired"      # Agent paired with a human
    HUMAN_SHADOW = "human_shadow"      # Agent acting as human representative
    STANDALONE_AGENT = "standalone_agent"  # Independent agent

class AgentHierarchyLevel(str, Enum):
    BOSS = "boss"          # Top-level decision making agent
    SUB_AGENT = "sub_agent"  # Subordinate agent
```

### Agent Configuration

**Before:**
```python
AgentConfig(
    name="My Agent",
    type=AgentType.AGENTIC,
    capabilities=["analysis"],
    model_name="gpt-4"
)
```

**After:**
```python
# Standalone Agent (Boss)
AgentConfig(
    name="Boss Agent",
    role_type=AgentRoleType.STANDALONE_AGENT,
    hierarchy_level=AgentHierarchyLevel.BOSS,
    capabilities=["strategic_planning", "decision_making"],
    model_name="gpt-4"
)

# Standalone Agent (Sub-agent)
AgentConfig(
    name="Sub Agent",
    role_type=AgentRoleType.STANDALONE_AGENT,
    hierarchy_level=AgentHierarchyLevel.SUB_AGENT,
    parent_agent_id="boss_agent_id",
    capabilities=["data_analysis"],
    model_name="gpt-3.5-turbo"
)

# Human-Paired Agent
AgentConfig(
    name="Collaborative Agent",
    role_type=AgentRoleType.HUMAN_PAIRED,
    human_pairing=HumanPairing(
        human_id="user123",
        human_name="John Doe",
        contact_method="slack",
        contact_details={"channel": "#ai-collab"}
    ),
    capabilities=["collaboration", "communication"]
)

# Human Shadow Agent
AgentConfig(
    name="Executive Shadow",
    role_type=AgentRoleType.HUMAN_SHADOW,
    represented_human_id="exec123",
    represented_human_name="Jane Executive",
    shadow_permissions=["approve_budgets_under_10k", "schedule_meetings"],
    capabilities=["decision_making", "scheduling"]
)
```

## Migration Steps

### Step 1: Update Imports

```python
# Add new imports
from .models import (
    AgentRoleType, AgentHierarchyLevel, AgentStatus, HumanPairing
)
from .role_based_agents import (
    StandaloneAgent, HumanPairedAgent, HumanShadowAgent
)
from .role_based_agent_manager import RoleBasedAgentManager
```

### Step 2: Replace AgentManager

**Before:**
```python
agent_manager = AgentManager(task_manager, mcp_manager)
```

**After:**
```python
agent_manager = RoleBasedAgentManager(task_manager, mcp_manager)
```

### Step 3: Update Agent Creation

**Before:**
```python
# Creating agentic agents
config = AgentConfig(
    name="Data Agent",
    type=AgentType.AGENTIC,
    capabilities=["data_analysis"]
)
agent = agent_manager.create_agent(config)
```

**After:**
```python
# Create boss agent
boss_agent = await agent_manager.create_boss_agent(
    name="System Boss",
    capabilities=["strategic_planning", "decision_making"]
)

# Create sub-agent
sub_agent = await agent_manager.create_sub_agent(
    name="Data Agent",
    capabilities=["data_analysis"],
    parent_agent_id=boss_agent.config.id
)

# Create human-paired agent
pairing = HumanPairing(
    human_id="user123",
    human_name="Analyst Jane",
    contact_method="slack",
    contact_details={"channel": "#data-team"}
)
paired_agent = await agent_manager.create_human_paired_agent(
    name="Collaborative Data Agent",
    human_pairing=pairing,
    capabilities=["data_analysis", "collaboration"]
)

# Create shadow agent
shadow_agent = await agent_manager.create_human_shadow_agent(
    name="Manager Shadow",
    represented_human_id="mgr123",
    represented_human_name="Bob Manager",
    shadow_permissions=["approve_routine_requests"],
    capabilities=["decision_making"]
)
```

### Step 4: Update Task Assignment

**Before:**
```python
task = TaskDefinition(
    name="Analysis Task",
    description="Analyze the data",
    function_name="analyze_data"
)
agent = agent_manager.assign_task_to_best_agent(task)
```

**After:**
```python
# Basic task (will go to appropriate standalone agent)
task = TaskDefinition(
    name="Analysis Task",
    description="Analyze the data",
    function_name="analyze_data",
    required_capabilities=["data_analysis"]
)

# Strategic task (will prefer boss agent)
strategic_task = TaskDefinition(
    name="Strategic Decision",
    description="Make strategic decision",
    function_name="strategic_decision",
    requires_boss_level=True
)

# Collaborative task (will prefer human-paired agent)
collab_task = TaskDefinition(
    name="Creative Review",
    description="Review creative content with human",
    function_name="creative_review",
    requires_human_interaction=True,
    preferred_role_type=AgentRoleType.HUMAN_PAIRED
)

# Shadow task (will prefer shadow agent)
approval_task = TaskDefinition(
    name="Approve Request",
    description="Approve routine request",
    function_name="approve_request",
    required_permissions=["approve_routine_requests"],
    preferred_role_type=AgentRoleType.HUMAN_SHADOW
)

# Assign tasks
agents = []
for task in [task, strategic_task, collab_task, approval_task]:
    agent = await agent_manager.assign_task_to_best_agent(task)
    agents.append(agent)
```

## Backward Compatibility

The new system maintains backward compatibility:

1. **AgentType still works**: The old `AgentType` enum is aliased to `AgentRoleType`
2. **Old configurations**: Existing agent configs will still work with some limitations
3. **Legacy methods**: Most existing methods are still available

### Compatibility Layer

```python
# This still works
config = AgentConfig(
    name="Legacy Agent",
    type=AgentType.AGENTIC,  # Maps to STANDALONE_AGENT
    capabilities=["general"]
)

# Access through new properties
assert config.role_type == AgentRoleType.STANDALONE_AGENT
assert config.type == config.role_type  # Backward compatibility
```

## New Features

### 1. Human-Paired Collaboration

```python
# Set up real-time collaboration
pairing = HumanPairing(
    human_id="designer123",
    human_name="Alice Designer",
    contact_method="slack",
    collaboration_level="intensive",  # real-time collaboration
    communication_frequency="real_time"
)

agent = await agent_manager.create_human_paired_agent(
    "Design Collaborator",
    pairing,
    ["design_review", "content_creation"]
)
```

### 2. Human Shadow Representation

```python
# Create shadow with specific permissions
shadow = await agent_manager.create_human_shadow_agent(
    "Executive Shadow",
    "exec123",
    "Bob Executive",
    shadow_permissions=[
        "approve_budgets_under_5k",
        "schedule_meetings",
        "respond_to_routine_emails"
    ]
)

# Tasks requiring higher permissions will be escalated
```

### 3. Hierarchical Organization

```python
# Get hierarchical view
hierarchy = agent_manager.get_hierarchy_view()
print(f"Boss agents: {len(hierarchy['boss_agents'])}")
print(f"Sub-agents: {len(hierarchy['sub_agents'])}")

# Scale agents by type
await agent_manager.scale_agents(
    target_standalone=5,
    target_paired=2, 
    target_shadow=1
)
```

### 4. Enhanced Statistics

```python
# Get comprehensive stats
stats = agent_manager.get_agent_stats()
print(f"Agents by role: {stats['agents_by_role']}")
print(f"Agents by status: {stats['agents_by_status']}")

# Get specific agent types
paired_agents = agent_manager.get_human_paired_agents()
shadow_agents = agent_manager.get_human_shadow_agents()
```

## Best Practices

### 1. Agent Role Selection

- **Use Standalone Agents** for independent tasks that don't require human interaction
- **Use Human-Paired Agents** for creative work, complex decisions, or tasks requiring human insight
- **Use Human Shadow Agents** for routine decisions that a human would normally make

### 2. Hierarchy Design

- **Boss Agents**: Strategic decisions, high-level coordination, complex problem solving
- **Sub-Agents**: Specialized tasks, routine operations, data processing

### 3. Human Integration

- **Paired Agents**: Real-time collaboration, creative partnerships
- **Shadow Agents**: Routine decisions, automated approvals, representation

### 4. Task Design

```python
# Include role preferences in task definitions
task = TaskDefinition(
    name="Content Strategy",
    description="Develop content strategy",
    function_name="content_strategy",
    preferred_role_type=AgentRoleType.HUMAN_PAIRED,
    requires_human_interaction=True,
    required_capabilities=["content_creation", "strategy"]
)
```

## Testing Your Migration

```python
async def test_migration():
    """Test the migrated system"""
    
    # 1. Create all agent types
    manager = RoleBasedAgentManager(task_manager, mcp_manager)
    
    boss = await manager.create_boss_agent("Test Boss")
    sub = await manager.create_sub_agent("Test Sub")
    
    pairing = HumanPairing(
        human_id="test", human_name="Test Human", 
        contact_method="slack"
    )
    paired = await manager.create_human_paired_agent("Test Paired", pairing)
    
    shadow = await manager.create_human_shadow_agent(
        "Test Shadow", "human123", "Test Human", ["test_permission"]
    )
    
    # 2. Test task assignment
    tasks = [
        TaskDefinition(name="Strategic", requires_boss_level=True),
        TaskDefinition(name="Routine", required_capabilities=["general"]),
        TaskDefinition(name="Creative", requires_human_interaction=True),
        TaskDefinition(name="Approval", required_permissions=["test_permission"])
    ]
    
    for task in tasks:
        agent = await manager.assign_task_to_best_agent(task)
        print(f"{task.name} → {agent.config.name if agent else 'None'}")
    
    # 3. Verify statistics
    stats = manager.get_agent_stats()
    assert stats['total_agents'] == 4
    assert stats['agents_by_role']['standalone_agent'] == 2
    assert stats['agents_by_role']['human_paired'] == 1
    assert stats['agents_by_role']['human_shadow'] == 1

# Run test
await test_migration()
```

## Troubleshooting

### Common Issues

1. **"Standalone agents must have hierarchy_level specified"**
   - Solution: Add `hierarchy_level=AgentHierarchyLevel.BOSS` or `AgentHierarchyLevel.SUB_AGENT`

2. **"Human-paired agents must have human_pairing configuration"**
   - Solution: Provide a `HumanPairing` object in the agent config

3. **"Human-shadow agents must have represented_human_id and represented_human_name"**
   - Solution: Specify the human being represented by the shadow agent

### Performance Considerations

1. **Human-paired agents** have lower concurrent task limits due to human interaction requirements
2. **Shadow agents** may escalate tasks, adding latency for complex decisions
3. **Boss agents** should be used sparingly for strategic tasks only

### Migration Checklist

- [ ] Updated imports to include new role-based classes
- [ ] Replaced `AgentManager` with `RoleBasedAgentManager`  
- [ ] Updated agent creation to use role-specific methods
- [ ] Modified task definitions to include role preferences
- [ ] Tested all three agent types
- [ ] Verified backward compatibility with existing code
- [ ] Updated monitoring/statistics gathering
- [ ] Documented new agent roles for your team

## Support

For questions about the migration:

1. Check the examples in `examples/role_based_agent_examples.py`
2. Run the test suite in `test_role_based_agents.py`
3. Review the API documentation for detailed method signatures