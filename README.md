# Nox: An Autonomous AI Agent Core

## Overview

Nox is not just a chatbot. It is an advanced, autonomous AI agent core designed for complex, multi-step tasks and persistent, stateful interaction. Built on a sophisticated microservices architecture and powered by the LangGraph engine, Nox represents a shift from simple prompt-response models to a genuine thinking and acting entity.

The core philosophy of Nox is to create a true AI partner, capable of reasoning, planning, and executing tasks while maintaining a continuous, evolving memory of its interactions and experiences.

## Key Features

* **Agentic Mind:** At its heart, Nox utilizes the **LangGraph** library to implement a **ReAct (Reason + Act) cycle**. This allows the agent to think iteratively, form plans, use tools, observe the results, and adapt its strategy until the user's goal is achieved.
* **Dual-Horizon Memory:** Nox possesses a two-tiered memory system for robust contextual understanding:
    * **Short-Term Memory:** A conversational buffer ensures immediate context is never lost during an ongoing dialogue.
    * **Long-Term Memory:** Powered by a `LanceDB` vector store, Nox archives the essence of important interactions, allowing it to retrieve relevant past experiences to inform current decisions.
* **Extensible Toolbelt:** Nox is designed to interact with the world through a flexible set of tools. The initial implementation includes seamless integration with Home Assistant, enabling it to control smart home devices and perceive the physical environment.
* **Microservice Architecture:** The entire ecosystem is orchestrated via Docker Compose, separating concerns into independent, resilient services:
    * **`nox-core`**: The central brain running the LangGraph agent.
    * **`ollama`**: The heart, serving the foundational language model.
    * **`homeassistant`**: The hands, providing the interface to the real world.
    * **`telegram_bot`**: The voice and ears, facilitating natural communication with the user.

## Architecture

Nox is built as a distributed system of interconnected services. A user's message, received via the Telegram bot, triggers the `nox-core` agent. The agent, leveraging its dual memory, enters a reasoning loop powered by LangGraph. It can autonomously decide to call upon its tools, such as the Home Assistant integration, to gather information or perform actions. The results of these actions are fed back into the reasoning loop, allowing Nox to refine its plan and ultimately provide a comprehensive, context-aware response to the user.

## Author

* **Architect & Lead Developer:** Gemini