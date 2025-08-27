"""
Examples demonstrating the new role-based agent system
"""

import asyncio
from datetime import datetime

from ..models import (
    AgentConfig, AgentRoleType, AgentHierarchyLevel, AgentStatus,
    TaskDefinition, TaskPriority, HumanPairing, PromptSignature
)
from ..role_based_agent_manager import RoleBasedAgentManager
from ..task_manager import TaskManager
from ..mcp import MCPManager


async def example_standalone_agents():
    """Example: Creating and using standalone agents (boss and sub-agents)"""
    print("=== Standalone Agents Example ===")
    
    # Mock managers (in real usage, these would be properly initialized)
    task_manager = TaskManager()
    mcp_manager = MCPManager()
    
    # Create the role-based agent manager
    agent_manager = RoleBasedAgentManager(task_manager, mcp_manager)
    
    # 1. Create a boss agent
    print("Creating boss agent...")
    boss_agent = await agent_manager.create_boss_agent(
        name="Strategic Boss",
        capabilities=[
            "strategic_planning", "decision_making", "task_delegation",
            "system_coordination", "agent_management", "resource_allocation"
        ]
    )
    print(f"Boss agent created: {boss_agent.config.name}")
    
    # 2. Create sub-agents
    print("\nCreating sub-agents...")
    
    data_analyst = await agent_manager.create_sub_agent(
        name="Data Analyst Agent",
        capabilities=["data_analysis", "pattern_recognition", "reporting"],
        parent_agent_id=boss_agent.config.id
    )
    
    task_executor = await agent_manager.create_sub_agent(
        name="Task Executor Agent", 
        capabilities=["task_execution", "process_automation", "system_integration"],
        parent_agent_id=boss_agent.config.id
    )
    
    print(f"Sub-agents created: {data_analyst.config.name}, {task_executor.config.name}")
    
    # 3. Create tasks for different agents
    print("\nCreating and assigning tasks...")
    
    strategic_task = TaskDefinition(
        name="Quarterly Planning",
        description="Plan Q4 strategy and resource allocation",
        function_name="strategic_planning",
        priority=TaskPriority.HIGH,
        requires_boss_level=True
    )
    
    analysis_task = TaskDefinition(
        name="Sales Data Analysis",
        description="Analyze Q3 sales performance data",
        function_name="data_analysis",
        priority=TaskPriority.MEDIUM,
        required_capabilities=["data_analysis", "reporting"]
    )
    
    automation_task = TaskDefinition(
        name="Process Automation",
        description="Automate customer onboarding workflow",
        function_name="process_automation", 
        priority=TaskPriority.LOW,
        required_capabilities=["task_execution", "process_automation"]
    )
    
    # 4. Assign tasks to best agents
    assigned_agents = {}
    for task in [strategic_task, analysis_task, automation_task]:
        agent = await agent_manager.assign_task_to_best_agent(task)
        assigned_agents[task.name] = agent.config.name if agent else "No suitable agent"
        print(f"Task '{task.name}' assigned to: {assigned_agents[task.name]}")
    
    # 5. Get hierarchy view
    print("\nHierarchy view:")
    hierarchy = agent_manager.get_hierarchy_view()
    print(f"Boss agents: {len(hierarchy['boss_agents'])}")
    print(f"Sub-agents: {len(hierarchy['sub_agents'])}")
    for rel in hierarchy['hierarchy_relationships']:
        print(f"  └─ {rel['child_name']} reports to {rel['parent_id']}")
    
    return agent_manager


async def example_human_paired_agents():
    """Example: Creating and using human-paired collaborative agents"""
    print("\n=== Human-Paired Agents Example ===")
    
    task_manager = TaskManager()
    mcp_manager = MCPManager()
    agent_manager = RoleBasedAgentManager(task_manager, mcp_manager)
    
    # 1. Create human pairing configurations
    print("Setting up human-agent pairings...")
    
    # Marketing team pairing
    marketing_pairing = HumanPairing(
        human_id="user-001",
        human_name="Sarah Marketing",
        contact_method="slack",
        contact_details={"channel": "#marketing-ai"},
        collaboration_level="intensive",
        communication_frequency="real_time"
    )
    
    # Sales team pairing
    sales_pairing = HumanPairing(
        human_id="user-002", 
        human_name="Mike Sales",
        contact_method="close_crm",
        contact_details={"user_id": "mike.sales@company.com"},
        collaboration_level="standard",
        communication_frequency="hourly"
    )
    
    # 2. Create human-paired agents
    marketing_agent = await agent_manager.create_human_paired_agent(
        name="Marketing Collaboration Agent",
        human_pairing=marketing_pairing,
        capabilities=["content_creation", "campaign_analysis", "market_research", "collaboration"]
    )
    
    sales_agent = await agent_manager.create_human_paired_agent(
        name="Sales Support Agent",
        human_pairing=sales_pairing,
        capabilities=["lead_qualification", "crm_management", "sales_analysis", "collaboration"]
    )
    
    print(f"Created paired agents: {marketing_agent.config.name}, {sales_agent.config.name}")
    
    # 3. Create collaborative tasks
    collaborative_tasks = [
        TaskDefinition(
            name="Campaign Strategy",
            description="Develop Q4 marketing campaign strategy",
            function_name="campaign_strategy",
            requires_human_interaction=True,
            preferred_role_type=AgentRoleType.HUMAN_PAIRED
        ),
        TaskDefinition(
            name="Lead Scoring Model",
            description="Update lead scoring algorithm based on recent data",
            function_name="lead_scoring",
            requires_human_interaction=True,
            preferred_role_type=AgentRoleType.HUMAN_PAIRED
        )
    ]
    
    # 4. Assign collaborative tasks
    print("\nAssigning collaborative tasks...")
    for task in collaborative_tasks:
        agent = await agent_manager.assign_task_to_best_agent(task)
        if agent:
            print(f"Task '{task.name}' assigned to {agent.config.name} (paired with {agent.human_pairing.human_name})")
    
    # 5. Show paired agent details
    print("\nHuman-paired agent details:")
    paired_agents = agent_manager.get_human_paired_agents()
    for agent_info in paired_agents:
        pairing = agent_info.get('pairing_details', {})
        print(f"  Agent: {agent_info['name']}")
        print(f"    Paired with: {pairing.get('human_name')}")
        print(f"    Collaboration level: {pairing.get('collaboration_level')}")
        print(f"    Contact method: {pairing.get('contact_method')}")
    
    return agent_manager


async def example_human_shadow_agents():
    """Example: Creating and using human shadow agents"""
    print("\n=== Human Shadow Agents Example ===")
    
    task_manager = TaskManager()
    mcp_manager = MCPManager()
    agent_manager = RoleBasedAgentManager(task_manager, mcp_manager)
    
    # 1. Create shadow agents for different executives
    print("Creating shadow agents for executives...")
    
    # CEO shadow
    ceo_shadow = await agent_manager.create_human_shadow_agent(
        name="CEO Shadow Agent",
        represented_human_id="ceo-001",
        represented_human_name="John CEO",
        shadow_permissions=[
            "approve_budgets_under_10k",
            "schedule_meetings",
            "respond_to_routine_emails",
            "make_operational_decisions",
            "delegate_tasks"
        ],
        capabilities=["executive_decision_making", "strategic_thinking", "communication"]
    )
    
    # CFO shadow
    cfo_shadow = await agent_manager.create_human_shadow_agent(
        name="CFO Shadow Agent",
        represented_human_id="cfo-001", 
        represented_human_name="Jane CFO",
        shadow_permissions=[
            "approve_expenses_under_5k",
            "review_financial_reports",
            "update_budget_forecasts",
            "process_vendor_payments"
        ],
        capabilities=["financial_analysis", "budget_management", "risk_assessment"]
    )
    
    print(f"Created shadow agents: {ceo_shadow.config.name}, {cfo_shadow.config.name}")
    
    # 2. Create tasks that shadows can handle
    shadow_tasks = [
        TaskDefinition(
            name="Approve Team Lunch Budget",
            description="Approve $500 budget for team lunch event",
            function_name="approve_budget",
            required_permissions=["approve_budgets_under_10k"],
            preferred_role_type=AgentRoleType.HUMAN_SHADOW
        ),
        TaskDefinition(
            name="Schedule Board Meeting",
            description="Schedule Q4 board meeting with all members",
            function_name="schedule_meeting",
            required_permissions=["schedule_meetings"],
            preferred_role_type=AgentRoleType.HUMAN_SHADOW
        ),
        TaskDefinition(
            name="Approve Software License", 
            description="Approve $15k software license renewal",
            function_name="approve_expense",
            required_permissions=["approve_budgets_under_10k"],  # This should escalate
            preferred_role_type=AgentRoleType.HUMAN_SHADOW
        )
    ]
    
    # 3. Assign tasks to shadow agents
    print("\nAssigning tasks to shadow agents...")
    for task in shadow_tasks:
        agent = await agent_manager.assign_task_to_best_agent(task)
        if agent:
            represented = agent.config.represented_human_name
            print(f"Task '{task.name}' assigned to {agent.config.name} (representing {represented})")
            
            # Show if task would be escalated
            if hasattr(task, 'required_permissions'):
                can_handle = all(perm in agent.config.shadow_permissions for perm in task.required_permissions)
                if not can_handle:
                    print(f"  ⚠️  This task will likely be escalated to {represented}")
    
    # 4. Show shadow agent details
    print("\nShadow agent details:")
    shadow_agents = agent_manager.get_human_shadow_agents()
    for agent_info in shadow_agents:
        shadow_details = agent_info.get('shadow_details', {})
        print(f"  Agent: {agent_info['name']}")
        print(f"    Represents: {shadow_details.get('represented_human_name')}")
        print(f"    Permissions: {', '.join(shadow_details.get('shadow_permissions', []))}")
    
    return agent_manager


async def example_mixed_agent_ecosystem():
    """Example: Complete ecosystem with all agent types working together"""
    print("\n=== Mixed Agent Ecosystem Example ===")
    
    task_manager = TaskManager()
    mcp_manager = MCPManager() 
    agent_manager = RoleBasedAgentManager(task_manager, mcp_manager)
    
    # 1. Create the complete ecosystem
    print("Building complete agent ecosystem...")
    
    # Boss agent
    boss = await agent_manager.create_boss_agent("System Boss")
    
    # Sub-agents for different functions
    analyst = await agent_manager.create_sub_agent("Data Analyst", ["data_analysis"])
    executor = await agent_manager.create_sub_agent("Task Executor", ["automation"])
    
    # Human-paired agent for creative work
    creative_pairing = HumanPairing(
        human_id="creative-001",
        human_name="Alice Creative",
        contact_method="slack",
        contact_details={"channel": "#creative-ai"}
    )
    creative_agent = await agent_manager.create_human_paired_agent(
        "Creative Collaboration Agent",
        creative_pairing,
        ["content_creation", "design_review"]
    )
    
    # Shadow agent for routine approvals
    manager_shadow = await agent_manager.create_human_shadow_agent(
        "Manager Shadow",
        "manager-001",
        "Bob Manager", 
        ["approve_routine_requests", "schedule_meetings"],
        ["decision_making"]
    )
    
    # 2. Create diverse tasks that require different agent types
    diverse_tasks = [
        # Strategic task - should go to boss
        TaskDefinition(
            name="Annual Strategy Review",
            description="Review and update annual business strategy",
            function_name="strategic_review",
            requires_boss_level=True
        ),
        
        # Data task - should go to analyst
        TaskDefinition(
            name="Customer Behavior Analysis", 
            description="Analyze customer behavior patterns",
            function_name="behavior_analysis",
            required_capabilities=["data_analysis"]
        ),
        
        # Creative task - should go to human-paired agent
        TaskDefinition(
            name="Marketing Video Concept",
            description="Develop concept for new marketing video",
            function_name="creative_concept",
            requires_human_interaction=True,
            preferred_role_type=AgentRoleType.HUMAN_PAIRED
        ),
        
        # Routine approval - should go to shadow agent
        TaskDefinition(
            name="Approve Team Training",
            description="Approve training request for development team", 
            function_name="approve_training",
            required_permissions=["approve_routine_requests"],
            preferred_role_type=AgentRoleType.HUMAN_SHADOW
        ),
        
        # Automation task - should go to executor
        TaskDefinition(
            name="Automate Report Generation",
            description="Set up automated weekly report generation",
            function_name="setup_automation",
            required_capabilities=["automation"]
        )
    ]
    
    # 3. Assign all tasks and show the distribution
    print("\nTask assignment across mixed ecosystem:")
    assignment_summary = {}
    
    for task in diverse_tasks:
        agent = await agent_manager.assign_task_to_best_agent(task)
        if agent:
            agent_type = agent.config.role_type.value
            if agent.config.role_type == AgentRoleType.STANDALONE_AGENT:
                agent_type += f" ({agent.config.hierarchy_level.value})"
            
            assignment_summary[task.name] = {
                "agent": agent.config.name,
                "type": agent_type
            }
            print(f"  '{task.name}' → {agent.config.name} ({agent_type})")
    
    # 4. Show ecosystem statistics
    print("\nEcosystem statistics:")
    stats = agent_manager.get_agent_stats()
    print(f"  Total agents: {stats['total_agents']}")
    for role_type, count in stats['agents_by_role'].items():
        if count > 0:
            print(f"  {role_type.replace('_', ' ').title()}: {count}")
    
    return agent_manager, assignment_summary


async def main():
    """Run all examples"""
    print("🤖 Role-Based Agent System Examples")
    print("=" * 50)
    
    try:
        # Run each example
        await example_standalone_agents()
        await example_human_paired_agents() 
        await example_human_shadow_agents()
        ecosystem_manager, assignments = await example_mixed_agent_ecosystem()
        
        print("\n✅ All examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Standalone agents with boss/sub-agent hierarchy")
        print("  • Human-paired agents for collaborative work")
        print("  • Human shadow agents for routine decision making")
        print("  • Intelligent task assignment based on agent capabilities")
        print("  • Mixed ecosystem with all agent types working together")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())