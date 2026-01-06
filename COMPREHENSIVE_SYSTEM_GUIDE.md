# AI Assistant: Comprehensive System Guide

This master document provides a full technical overview of the Market Research AI Assistant, from file upload to deep data analysis.

---

## 1. System Philosophy: The "Multi-Layer" Memory
The system is designed to be fast, cost-effective, and secure. It uses three layers of memory to handle your questions:

| Layer | Type | Store | Best for... |
| :--- | :--- | :--- | :--- |
| **Registry** | RAM (Fast) | Backend | "What files do I have?" |
| **Indexing** | Search (Persist) | AI Search | "Summarize this PDF" |
| **Insight** | Raw (Deep) | Blob + Databricks | "Calculate average revenue" |

---

## 2. The Data Journey (Step-by-Step)

### A. Filing & Upload
When you upload a file, the system performs a triple-action:
1.  **Storage**: The raw bytes go to **Azure Blob Storage**.
2.  **Registry**: The metadata (name, ID, size) is saved in `shared_state.py`. This is our "Locker List."
3.  **Indexing**: The text is split into chunks and pushed to **Azure AI Search**.

### B. Accessing the Data
*   **Researcher Agent**: Accesses the **Registry** and **Index**. It sees what you see but doesn't "run" the data.
*   **Python Agent**: Accesses the **Raw Storage** via Databricks. It "runs" the math.

---

## 3. Azure Databricks Integration

### The Stalling Point: Mounting
Initially, we tried to "Mount" storage (make it a local drive). This was blocked by your workspace's security policy (`FeatureDisabledException`). Mounting is an "Infrastructural Change" that often requires admin-level permissions.

### The Solution: Direct Access Handshake
We switched to a **Session-Level Handshake**. 
*   **Mechanism**: `spark.conf.set()`
*   **How it works**: Instead of modifying the building, we store the **SAS Token** (Security Pass) in the Spark engine's memory for the current session.
*   **Pathing**: Files are accessed via the `wasbs://` protocol.

---

## 4. Key Configuration Points

### Environment Variables (.env)
*   `AZURE_STORAGE_SAS_TOKEN`: Must be a single line, no spaces around `=`, and no leading `?`.
*   `DATABRICKS_CLUSTER_ID`: `1227-101008-87vvcqgw`

### Critical Permissions
To allow Databricks to read your data, the SAS Token generated in Azure **MUST** have the **"List"** permission checked, along with Service, Container, and Object resource types.

---

## 5. Decision Logic (The "Orchestrator")

The Orchestrator determines which agent to use:
*   **Schema/Listing** -> Researcher Agent (No Databricks cost).
*   **Calculation/Deep Insight** -> Python Agent (Triggers Databricks).

---

## 6. How to Run Analysis (Manually or via AI)
To query a file like `test_data.csv` in a notebook, use:
```python
file_path = "wasbs://mrfileuploads@straccai.blob.core.windows.net/test_data.csv"
df = spark.read.option("header", "true").csv(file_path)
display(df)
```

---

*This guide serves as the final documentation for the core backend and analysis engine of the AI Assistant project.*
