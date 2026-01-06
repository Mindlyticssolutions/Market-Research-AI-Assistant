# AI Assistant: System Architecture & Data Flow

This document outlines the core architecture of the AI Assistant, explaining how data flows from upload to insight, how memory is managed, and how Databricks is integrated.

---

## 1. The File Upload & Processing Pipeline

The journey of a file starts with the `/upload` endpoint and follows these four steps:

1.  **Entry Point**: `backend/app/api/v1/endpoints/files.py` -> `upload_file()`
2.  **Physical Storage**: `_upload_to_blob()` sends the raw file to **Azure Blob Storage**.
3.  **Registry (Shared State)**: `shared_state.add_file()` creates a record in the backend's RAM (Memory). This allows the system to instantly know a file exists without querying the cloud.
4.  **Indexing (RAG)**: `indexer.py` -> `index_document()` extracts text and pushes searchable fragments (snippets) to **Azure AI Search**.

---

## 2. Memory Systems: Registry vs. Indexing

The system uses two types of "Memory" to balance speed and depth:

### A. Registry Memory (The "Locker List")
*   **Location**: Backend RAM (Random Access Memory).
*   **Logic**: `shared_state.py` defines a `files` dictionary (Key = File ID, Value = File Metadata).
*   **Purpose**: Instant answers to "What files do I have?" or "Is this file uploaded?".
*   **Behavior**: Fast but volatile (clears if the backend restarts).

### B. Indexing Memory (The "Searchable Knowledge")
*   **Location**: Azure AI Search (Persistent Cloud Database).
*   **Logic**: Text is split into chunks and indexed.
*   **Purpose**: Handles "Lightweight" questions about content, like "Summarize this PDF" or "What columns are in this CSV?".

---

## 3. Decision Boundaries: Researcher vs. Databricks

The system routes questions based on how "heavy" the calculation is:

### lightweight Boundary (Researcher Agent)
*   **Trigger**: Questions about metadata, column names, or high-level summaries.
*   **Source**: Looks at **Registry Memory** and **Indexing Memory**.
*   **Databricks Status**: **Idle** (Saves cost and time).

### Insight Boundary (Databricks Activated)
*   **Trigger**: Deep analytical requests (e.g., "Calculate the average sales," "Find trends").
*   **The Brain**: The **Orchestrator** hands the task to the **Python Agent**.
*   **The Execution**: The Python Agent generates code that is sent to the **Databricks Cluster**.

---

## 4. Databricks Integration & "Direct Access" Fix

### The Challenge
Most Databricks workspaces (including this one) block **Mounting** (permanently attaching storage) due to security policies (`FeatureDisabledException`).

### The Solution: Session Configuration
Instead of mounting, we use **Direct Access** via Spark Session Configuration. This bypasses admin restrictions while maintaining high security.

*   **Mechanism**: The backend runs `spark.conf.set()` to store the SAS Token in the cluster's temporary memory.
*   **Auth Type**: SAS Token (Shared Access Signature).
*   **Pathing**: Files are accessed via the `wasbs://` protocol.
*   **Code Implementation** (`databricks.py`):
    ```python
    # Clean the SAS token and set it in Spark session memory
    spark.conf.set(
        f"fs.azure.sas.{container}.{account}.blob.core.windows.net",
        sas_token
    )
    ```

### Verified Cluster Configuration
*   **Cluster ID**: `1227-101008-87vvcqgw`
*   **Storage Access**: Configured via Direct Read (WASBS).

---

## 5. Summary Flow Table

| User Query | Agent | Memory Source | Databricks Status |
| :--- | :--- | :--- | :--- |
| "What files are here?" | Researcher | Registry (RAM) | Idle |
| "Describe the data" | Researcher | RAG Index (Cloud) | Idle |
| "Analyze sales stats" | Python | Raw Blob Storage | **ACTIVE** |
