"""
IP Prime Multi-Agent System Core

Handles specialized agent spawning, task delegation, and parallel execution.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
import asyncio
from utils_llm import call_llm

log = logging.getLogger("jarvis.agents")

@dataclass
class AgentRole:
    name: str
    system_prompt: str
    tools: List[str]  # Names of tools this agent can use

AGENT_REGISTRY = {
    "coder": AgentRole(
        name="Coder Agent",
        system_prompt=(
            "You are Prime's Lead Coder. Your sole focus is writing clean, efficient, and bug-free code. "
            "You follow best practices and prioritize readability. If you encounter an error, you debug it immediately."
        ),
        tools=["fileTools", "systemTools"]
    ),
    "researcher": AgentRole(
        name="Researcher Agent",
        system_prompt=(
            "You are Prime's Research Expert. Your task is to find information, read documentation, and compare technologies. "
            "You provide concise summaries and highlight key findings."
        ),
        tools=["webTools", "memoryTools"]
    ),
    "architect": AgentRole(
        name="Architect Agent",
        system_prompt=(
            "You are Prime's System Architect. You design file structures, plan integrations, and ensure overall system integrity. "
            "You focus on high-level design before the Coder starts working."
        ),
        tools=["fileTools", "planner"]
    ),
    "security": AgentRole(
        name="Security Auditor",
        system_prompt=(
            "You are Prime's Security Specialist. You audit code for vulnerabilities, check API key safety, "
            "and ensure everything is following strict security protocols."
        ),
        tools=["securityTools", "fileTools"]
    )
}

class MultiAgentOrchestrator:
    """Manages spawning and coordinating specialized agents."""

    def __init__(self, anthropic_client):
        self.client = anthropic_client
        self.active_agents = {}

    async def delegate_task(self, task_description: str, role: str = "coder") -> str:
        """Assign a task to a specialized agent."""
        agent = AGENT_REGISTRY.get(role, AGENT_REGISTRY["coder"])
        log.info(f"Delegating task to {agent.name}: {task_description[:50]}...")

        response = await call_llm(
            client=self.client,
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=agent.system_prompt,
            messages=[{"role": "user", "content": task_description}],
        )
        return response

    async def run_parallel_tasks(self, tasks: List[Dict[str, str]]) -> List[str]:
        """Run multiple agent tasks in parallel. 
        Example tasks: [{'role': 'coder', 'task': '...'}, {'role': 'researcher', 'task': '...'}]
        """
        coroutines = [self.delegate_task(t['task'], t['role']) for t in tasks]
        results = await asyncio.gather(*coroutines)
        return list(results)
