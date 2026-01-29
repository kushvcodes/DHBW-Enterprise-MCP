import streamlit as st
import json
import os

def show_benchmark_results():
    st.title("📊 Benchmark Results")

    # Locate the benchmark files (assuming they are in the root folder, one level up from client)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, "..")

    # UI for selecting benchmark type
    benchmark_type = st.selectbox("Select Benchmark Type", ["SSE", "stdio"])

    if benchmark_type == "SSE":
        results_path = os.path.join(root_dir, "benchmark_results.json")
    else:
        results_path = os.path.join(root_dir, "benchmark_results_stdio.json")

    # Check if file exists
    if not os.path.exists(results_path):
        st.warning(f"File `{os.path.basename(results_path)}` not found.")
        st.info("💡 Please run the benchmark script in your terminal first:\n\n`python benchmark.py` (for SSE) or `python benchmark_stdio.py` (for Stdio)")
        return

    # Load Data
    try:
        with open(results_path, "r") as f:
            results = json.load(f)
    except json.JSONDecodeError:
        st.error("Error decoding the JSON file. It might be corrupted.")
        return

    # --- RENDER METADATA ---
    st.info(f"**Last Benchmark Run:** {results.get('last_run_utc', 'N/A')} ({results.get('type', 'N/A').upper()})")

    # --- RENDER TOOLS TABLE ---
    st.header("🛠️ Tool Benchmarks")
    
    col1, col2 = st.columns(2)
    col1.metric("Overall Avg Latency (Tools)", f"{results.get('overall_avg_latency_tools', 0):.2f} ms")
    
    tool_data = []
    for tool_name, tool_results in results.get("tools", {}).items():
        tool_data.append({
            "Tool": tool_name,
            "Avg Latency (ms)": f"{tool_results['avg_latency']:.2f}",
            "Total Time (ms)": f"{tool_results['total_time']:.2f}",
            "Success": tool_results['successes'],
            "Errors": tool_results['errors']
        })
    
    if tool_data:
        st.dataframe(tool_data, use_container_width=True)
    else:
        st.caption("No tool data available.")

    # --- RENDER RESOURCES TABLE ---
    st.header("📚 Resource Benchmarks")
    
    if results.get('resources'):
        col1.metric("Overall Avg Latency (Resources)", f"{results.get('overall_avg_latency_resources', 0):.2f} ms")
        
        resource_data = []
        for resource_name, resource_results in results.get("resources", {}).items():
            resource_data.append({
                "Resource": resource_name,
                "List Latency (ms)": f"{resource_results['list_latency_ms']:.2f}",
                "List Items": resource_results['list_item_count'],
                "Read Avg Latency (ms)": f"{resource_results['read_avg_latency_ms']:.2f}"
            })
        
        if resource_data:
            st.dataframe(resource_data, use_container_width=True)
    else:
        st.info("Resource benchmarking is not applicable (or no data found) for this run.")