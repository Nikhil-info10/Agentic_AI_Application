# AI Operations Assistant Using Agentic AI

An intelligent, multi-step IT Support Assistant utilizing **LangGraph** state graph routing and a persistent **SQLite database**. The assistant cleanly orchestrates task delegation between knowledge lookup tools and data modification endpoints while serving a chat interface via **Streamlit**.

## 🏗️ System Architecture

```mermaid
graph TD
    User([User Chat Input]) --> Streamlit[Streamlit Frontend App]
    Streamlit --> LG[LangGraph Runtime Engine]
    
    subgraph State Machine Workflow
        LG --> NodeAgent[Agent Node / LLM Decision]
        NodeAgent --> CondRoute{Tool Selection Needed?}
        
        CondRoute -- Yes --> NodeTools[Tool Execution Node]
        CondRoute -- No / Final Answer --> StateReturn[Return Final State]
        
        NodeTools --> kb_tool[kb_tool]
        NodeTools --> lookup_tool[lookup_tool]
        NodeTools --> create_tool[create_tool]
    end
    
    subgraph Data Layer
        kb_tool --> SQL[(SQLite DB: knowledge_base)]
        lookup_tool --> SQL[(SQLite DB: tickets)]
        create_tool --> SQL[(SQLite DB: tickets)]
    end
    
    StateReturn --> Streamlit
    SQL -. Real-time Sync .-> StreamlitSidebar[Streamlit Dynamic Sidebar Panel]
```

## 🛠️ Technology Stack
* **Language Framework:** Python 3.10+
* **Orchestration Matrix:** LangGraph / LangChain
* **LLM Engine:** OpenAI `gpt-4o-mini`
* **Data Storage:** SQLite Core Engine (Serverless Single-file DB)
* **User Interface:** Streamlit Engine

## 🚀 Step-by-Step Setup
1. **Clone or create** the structural directory files locally.
2. **Install all required dependencies**:
   ```bash
   pip install langchain-openai langgraph streamlit typing-extensions
   ```
3. **Configure Environment Secret**:
   ```bash
   export OPENAI_API_KEY="your-actual-api-key-here"
   ```
4. **Boot the application**:
   ```bash
   streamlit run app.py
   ```
   *Note: Running the application for the first time will automatically generate `it_support.db` and populate seed metrics.*

## 🔒 Key Design Decisions & Guardrails
* **Real-time State Refresh:** Streamlit's structural execution stack invokes `st.rerun()` directly after state loops complete to guarantee data matches mutations instantaneously without forcing mechanical manual resets.
* **Duplicate Prevention Check:** The database system queries existing tickets containing matching `Employee IDs` and structural issues before executing `INSERT` commands to enforce schema health cleanly.
