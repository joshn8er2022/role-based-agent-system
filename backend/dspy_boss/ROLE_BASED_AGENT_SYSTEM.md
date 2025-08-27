# Role-Based Agent System

## Overview

The new role-based agent system provides a flexible framework for different types of AI agents that can work independently, collaboratively with humans, or as human representatives. This system replaces the previous simple agent type system with a more sophisticated role-based approach.

## Agent Role Types

### 1. Human-Paired Agents (`HUMAN_PAIRED`)

**Purpose**: Agents that work in direct collaboration with humans for tasks requiring human insight, creativity, or decision-making.

**Key Features**:
- Real-time collaboration with assigned humans
- Configurable collaboration levels (light, standard, intensive)
- Human input integration for complex decisions
- Automatic task analysis to determine when human input is needed
- Multiple communication channels (Slack, CRM, email)

**Use Cases**:
- Creative content development
- Strategic planning with human oversight
- Complex problem-solving requiring domain expertise
- Quality review and approval workflows
- Customer-facing tasks requiring human judgment

**Example**:
```python
# Marketing team collaboration
marketing_pairing = HumanPairing(
    human_id="marketer_001",
    human_name="Sarah Johnson",
    contact_method="slack",
    contact_details={"channel": "#marketing-ai"},
    collaboration_level="intensive",
    communication_frequency="real_time"
)

marketing_agent = await agent_manager.create_human_paired_agent(
    name="Marketing Collaboration Agent",
    human_pairing=marketing_pairing,
    capabilities=["content_creation", "campaign_analysis", "market_research"]
)
```

### 2. Human Shadow Agents (`HUMAN_SHADOW`)

**Purpose**: Agents that act as representatives of humans in the background, making routine decisions and handling tasks on their behalf.

**Key Features**:
- Permission-based decision making
- Automatic escalation for tasks beyond permissions
- Human-like reasoning patterns
- Representation of specific individuals
- Configurable shadow permissions

**Use Cases**:
- Executive assistants for routine approvals
- Automated email responses in someone's style
- Routine decision-making within defined parameters
- Meeting scheduling and calendar management
- Low-level budget approvals and expense processing

**Example**:
```python
# CEO shadow for routine decisions
ceo_shadow = await agent_manager.create_human_shadow_agent(
    name="CEO Shadow Agent",
    represented_human_id="ceo_001",
    represented_human_name="John CEO",
    shadow_permissions=[
        "approve_budgets_under_10k",
        "schedule_meetings",
        "respond_to_routine_emails",
        "delegate_tasks"
    ],
    capabilities=["executive_decision_making", "scheduling", "communication"]
)
```

### 3. Standalone Agents (`STANDALONE_AGENT`)

**Purpose**: Independent agents that operate autonomously without direct human interaction. Can be organized in hierarchical structures.

**Hierarchy Levels**:
- **Boss Agents**: Top-level strategic decision makers
- **Sub-Agents**: Specialized task executors

**Key Features**:
- Autonomous operation
- Hierarchical organization (boss → sub-agents)
- Specialized capabilities
- Independent decision-making
- Task delegation capabilities (for boss agents)

**Use Cases**:
- Data processing and analysis
- System automation
- Strategic planning and coordination (boss level)
- Specialized task execution (sub-agent level)
- Background monitoring and maintenance

**Example**:
```python
# Create boss agent
boss_agent = await agent_manager.create_boss_agent(
    name="System Coordinator",
    capabilities=[
        "strategic_planning", "task_delegation", 
        "system_coordination", "resource_allocation"
    ]
)

# Create specialized sub-agent
data_agent = await agent_manager.create_sub_agent(
    name="Data Processing Agent",
    capabilities=["data_analysis", "pattern_recognition", "reporting"],
    parent_agent_id=boss_agent.config.id
)
```

## Agent Configuration

### Base Configuration

All agents share these common configuration elements:

```python
class AgentConfig(BaseModel):
    id: str                           # Unique identifier
    name: str                         # Human-readable name
    role_type: AgentRoleType         # The agent's role type
    description: Optional[str]        # Description of agent's purpose
    capabilities: List[str]           # What the agent can do
    max_concurrent_tasks: int         # Task capacity
    status: AgentStatus              # Current operational status
    
    # Performance tracking
    performance_score: float          # 0.0 to 1.0 performance rating
    total_tasks_completed: int        # Historical task count
    success_rate: float              # Success percentage
    average_response_time: float      # Average task completion time
    
    # AI/LLM Configuration
    model_name: Optional[str]         # LLM model to use
    prompt_signature: Optional[str]   # DSPY signature name
    llm_provider: Optional[str]       # LLM provider
```

### Role-Specific Configuration

#### Standalone Agents
```python
hierarchy_level: AgentHierarchyLevel  # BOSS or SUB_AGENT
parent_agent_id: Optional[str]        # For sub-agents, ID of parent
```

#### Human-Paired Agents
```python
human_pairing: HumanPairing           # Pairing configuration
```

#### Human Shadow Agents
```python
represented_human_id: str             # ID of represented human
represented_human_name: str           # Name of represented human
shadow_permissions: List[str]         # What shadow can do
```

## Task Assignment Intelligence

The system intelligently assigns tasks based on multiple factors:

### Assignment Criteria

1. **Role Suitability**: Match task requirements to agent role capabilities
2. **Hierarchy Preferences**: Strategic tasks prefer boss agents
3. **Capability Matching**: Required skills match agent capabilities
4. **Human Interaction Needs**: Route to appropriate human-interactive agents
5. **Permission Requirements**: Shadow agents check permission alignment
6. **Performance History**: Prefer high-performing agents
7. **Current Workload**: Balance load across available agents

### Task Definition Extensions

```python
class TaskDefinition(BaseModel):
    # Standard fields...
    
    # Role-based routing
    preferred_role_type: Optional[AgentRoleType]     # Preferred agent type
    requires_boss_level: bool = False                # Strategic task flag
    requires_human_interaction: bool = False         # Human input needed
    required_permissions: List[str] = []             # For shadow agents
    required_capabilities: List[str] = []            # Capability requirements
```

## Communication and Collaboration

### Human-Paired Agent Collaboration

1. **Task Analysis**: Agent analyzes if human input is needed
2. **Collaboration Request**: Formatted request sent to human
3. **Human Response**: Human provides input/approval/modification
4. **Task Execution**: Agent incorporates human input
5. **Result Notification**: Human notified of completion

### Human Shadow Agent Operations

1. **Permission Check**: Verify task is within shadow permissions
2. **Autonomous Execution**: Handle task as human representative
3. **Escalation**: Forward to human if beyond permissions
4. **Human-Style Reasoning**: Use human-like decision patterns

### Standalone Agent Coordination

1. **Boss-Level Decisions**: Strategic tasks routed to boss agents
2. **Task Delegation**: Boss agents can delegate to sub-agents
3. **Hierarchical Reporting**: Sub-agents report to parent agents
4. **Autonomous Operation**: Independent task execution

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Role-Based Agent Manager                  │
├─────────────────────────────────────────────────────────────┤
│  • Agent creation and lifecycle management                   │
│  • Intelligent task assignment                              │
│  • Performance monitoring                                   │
│  • Scaling and optimization                                 │
└─────────────────────────────────────────────────────────────┘
                               │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Standalone  │    │  Human-Paired   │    │  Human Shadow   │
│    Agents     │    │     Agents      │    │     Agents      │
├───────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Boss agents │    │ • Collaboration │    │ • Representation│
│ • Sub-agents  │    │ • Real-time     │    │ • Permissions   │
│ • Hierarchy   │    │   communication │    │ • Escalation    │
│ • Autonomy    │    │ • Human input   │    │ • Human-style   │
└───────────────┘    └─────────────────┘    └─────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Task Manager  │
                    │   MCP Manager   │
                    │   DSPY Engine   │
                    └─────────────────┘
```

## Performance and Monitoring

### Agent Statistics

```python
# System-wide statistics
stats = agent_manager.get_agent_stats()
{
    "total_agents": 8,
    "active_agents": 7,
    "agents_by_role": {
        "standalone_agent": 5,
        "human_paired": 2, 
        "human_shadow": 1
    },
    "agents_by_status": {
        "active": 5,
        "idle": 2,
        "busy": 1
    }
}

# Role-specific views
paired_agents = agent_manager.get_human_paired_agents()
shadow_agents = agent_manager.get_human_shadow_agents()
hierarchy = agent_manager.get_hierarchy_view()
```

### Performance Metrics

Each agent tracks:
- **Task completion rate**: Percentage of successful task completions
- **Response time**: Average time to complete tasks
- **Performance score**: Overall effectiveness rating (0.0-1.0)
- **Collaboration efficiency**: For human-interactive agents
- **Escalation rate**: For shadow agents

## Scaling and Optimization

### Automatic Scaling

The system can automatically scale agents based on workload:

```python
# Scale different agent types
await agent_manager.scale_agents(
    target_standalone=10,    # Scale standalone agents
    target_paired=3,         # Scale human-paired agents  
    target_shadow=2          # Scale shadow agents
)

# Remove idle agents
removed_count = agent_manager.remove_idle_agents(idle_timeout=1800)
```

### Load Balancing

- **Workload distribution**: Tasks distributed based on current agent load
- **Capability matching**: Tasks routed to agents with best skill match
- **Performance-based routing**: High-performing agents get priority
- **Automatic agent spawning**: New agents created during high load

## Integration Points

### MCP (Model Context Protocol) Integration

All agent types integrate with MCP servers for:
- External tool access
- Communication channels (Slack, CRM)
- Data sources and APIs
- System integrations

### DSPY Integration

Each agent type uses specialized DSPY signatures:
- **StandaloneAgentSignature**: For independent task execution
- **BossAgentSignature**: For strategic decisions and delegation  
- **HumanPairedSignature**: For collaborative task execution
- **HumanShadowSignature**: For human representative tasks

## Security and Permissions

### Permission Model

1. **Shadow Agents**: Explicit permission lists for what they can do
2. **Paired Agents**: Collaboration boundaries defined by pairing config
3. **Standalone Agents**: Capability-based access control
4. **System-Level**: Role-based access to system functions

### Audit Trail

All agent actions are logged with:
- Agent identity and role type
- Task details and outcomes
- Human interactions (for paired/shadow agents)
- Permission usage (for shadow agents)
- Performance metrics

## Benefits

### For Organizations

1. **Flexible Human-AI Collaboration**: Choose the right level of human involvement
2. **Scalable Automation**: Standalone agents handle routine tasks
3. **Executive Support**: Shadow agents provide 24/7 representation
4. **Intelligent Task Routing**: Right task to right agent type
5. **Performance Optimization**: Data-driven agent management

### For Developers

1. **Clear Role Separation**: Well-defined agent responsibilities
2. **Extensible Architecture**: Easy to add new role types
3. **Backward Compatibility**: Existing code continues to work
4. **Rich API**: Comprehensive management and monitoring
5. **Testing Support**: Built-in test framework

### For Users

1. **Natural Collaboration**: Human-paired agents feel like AI teammates
2. **Trusted Representation**: Shadow agents act reliably on their behalf
3. **Efficient Automation**: Standalone agents handle background tasks
4. **Predictable Behavior**: Each role type has consistent patterns
5. **Transparent Operations**: Clear visibility into agent activities

## Future Enhancements

### Planned Features

1. **Dynamic Role Adaptation**: Agents that can switch roles based on context
2. **Multi-Human Collaboration**: Agents paired with multiple humans
3. **Advanced Permission Systems**: More granular shadow agent permissions
4. **Cross-Agent Communication**: Direct agent-to-agent collaboration
5. **Learning and Adaptation**: Agents that improve over time

### Extension Points

1. **Custom Role Types**: Framework for adding new agent roles
2. **Integration Plugins**: Easy connection to new systems
3. **Custom Signatures**: Domain-specific DSPY signatures
4. **Workflow Integration**: Integration with workflow engines
5. **Analytics Dashboard**: Visual monitoring and management

## Getting Started

1. **Review the Migration Guide**: Understand how to transition existing code
2. **Run the Examples**: See the system in action with sample code
3. **Start Small**: Begin with one agent type and expand
4. **Test Thoroughly**: Use the provided test framework
5. **Monitor Performance**: Track agent effectiveness and optimize

The role-based agent system provides a powerful foundation for building sophisticated AI systems that can work independently, collaboratively, or as human representatives, depending on the specific needs of each task and organization.