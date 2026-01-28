import asyncio
import time
import json
import statistics
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_URL = "http://localhost:3000/sse"
STRESS_TEST_ITERATIONS = 500
STRESS_TEST_CONCURRENCY = 5

async def run_benchmark():
    print(f"🔬 Starting MCP Benchmark on {MCP_URL}...")
    
    all_results = {}
    resource_results = {}

    # METRIC 1: HANDSHAKE OVERHEAD
    print("\n--- 1. PROTOCOL OVERHEAD ANALYSIS ---")
    try:
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                
                # Measure Handshake Latency
                start_hs = time.time()
                await session.initialize()
                hs_latency = (time.time() - start_hs) * 1000
                
                # Measure Payload Size
                tools = await session.list_tools()
                
                payload_str = json.dumps([t.model_dump() for t in tools.tools])
                payload_size = len(payload_str)
                token_est = payload_size / 4
                
                print(f"✅ Handshake Latency: {hs_latency:.2f} ms")
                print(f"📦 Tool Definitions Payload: {payload_size} bytes")
                print(f"🪙 Estimated Token Cost: ~{int(token_est)} tokens")
                print(f"🛠️ Tools Found: {len(tools.tools)}")

        # METRIC 2: LATENCY STRESS TEST
        print(f"\n--- 2. LATENCY STRESS TEST (N={STRESS_TEST_ITERATIONS}, Concurrency={STRESS_TEST_CONCURRENCY}) ---")
        
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                all_tools = (await session.list_tools()).tools
                
                dummy_args = {
                    "get_student_grades": {"query": "s1001"},
                    "get_schedule": {"course_name": "Wirtschaftsinformatik"},
                    "get_all_professors": {},
                    "get_professor_for_module": {"module_name": "Web Engineering"},
                    "get_professor_info": {"prof_name": "Harsh"},
                    "get_events": {},
                    "query_academic_data": {"student_name": "Student One"}
                }

                for tool in all_tools:
                    if tool.name not in dummy_args:
                        print(f"\n⚠️ Skipping tool '{tool.name}': No dummy arguments defined.")
                        continue

                    print(f"\nBenchmarking Tool: '{tool.name}'...")
                    latencies = []
                    success_count = 0
                    error_count = 0
                    
                    tasks = []
                    for i in range(STRESS_TEST_ITERATIONS):
                        task = asyncio.create_task(session.call_tool(tool.name, dummy_args[tool.name]))
                        tasks.append(task)

                    start_time = time.time()
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    total_time = (time.time() - start_time) * 1000

                    for res in responses:
                        if isinstance(res, Exception):
                            error_count += 1
                        else:
                            success_count += 1
                    
                    avg_latency = total_time / STRESS_TEST_ITERATIONS
                    
                    all_results[tool.name] = {
                        "avg_latency": avg_latency,
                        "successes": success_count,
                        "errors": error_count,
                        "total_time": total_time
                    }

        # --- METRIC 3: RESOURCE BENCHMARKING ---
        print("\n\n--- 3. RESOURCE BENCHMARKING ---")
        async with sse_client(MCP_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                all_resources = (await session.list_resources()).resources

                print(f"Found {len(all_resources)} resource types to benchmark.")

                for resource_template in all_resources:
                    print(f"\nBenchmarking Resource: '{resource_template.name}'")

                    # 1. Benchmark list()
                    start_list = time.time()
                    list_result = await session.list_resources(resource_template.name)
                    list_latency = (time.time() - start_list) * 1000
                    
                    # 2. Benchmark read() for each item
                    read_latencies = []
                    if list_result.resources:
                        for resource_item in list_result.resources:
                            start_read = time.time()
                            await session.read_resource(resource_item.uri)
                            read_latency = (time.time() - start_read) * 1000
                            read_latencies.append(read_latency)
                    
                    avg_read_latency = statistics.mean(read_latencies) if read_latencies else 0
                    
                    resource_results[resource_template.name] = {
                        "list_latency_ms": list_latency,
                        "list_item_count": len(list_result.resources),
                        "read_avg_latency_ms": avg_read_latency
                    }

        # --- SAVE RESULTS TO FILE ---
        total_avg_latency_tools = statistics.mean([res["avg_latency"] for res in all_results.values()])
        total_avg_latency_resources = statistics.mean([res["read_avg_latency_ms"] for res in resource_results.values()]) if resource_results else 0
        
        final_results = {
            "last_run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": "sse",
            "tools": all_results,
            "resources": resource_results,
            "overall_avg_latency_tools": total_avg_latency_tools,
            "overall_avg_latency_resources": total_avg_latency_resources
        }
        
        with open("benchmark_results.json", "w") as f:
            json.dump(final_results, f, indent=2)
            
        print("\n\n✅ Benchmark complete. Results saved to benchmark_results.json")

        # --- FINAL AVERAGE CALCULATION ---
        print(f"\n\n=== OVERALL AVERAGE LATENCY (TOOLS): {total_avg_latency_tools:.2f} ms ===")
        print(f"=== OVERALL AVERAGE LATENCY (RESOURCES): {total_avg_latency_resources:.2f} ms ===")

    except Exception as e:
        print(f"\n❌ Error during benchmark: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
