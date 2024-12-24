from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

class CPUScheduling:
    def __init__(self):
        pass

    def round_robin(self, data):
        processes = data.get("processes")
        quantum = int(data.get("quantum"))

        if not processes or quantum is None:
            return {"error": "Missing required parameters."}

        try:
            arrival_time = [int(p['arrivalTime']) for p in processes]
            burst_time = [int(p['burstTime']) for p in processes]
        except ValueError:
            return {"error": "Invalid input: Ensure all times are integers."}

        n = len(processes)
        remaining_bt = burst_time.copy()
        waiting_time = [0] * n
        turnaround_time = [0] * n
        completion_time = [0] * n
        time = 0
        queue = []
        visited = [False] * n

        while True:
            for i in range(n):
                if arrival_time[i] <= time and not visited[i] and remaining_bt[i] > 0:
                    queue.append(i)
                    visited[i] = True

            if not queue:
                time += 1
                continue

            current = queue.pop(0)

            if remaining_bt[current] > quantum:
                time += quantum
                remaining_bt[current] -= quantum
            else:
                time += remaining_bt[current]
                remaining_bt[current] = 0
                completion_time[current] = time

            for i in range(n):
                if arrival_time[i] <= time and not visited[i] and remaining_bt[i] > 0:
                    queue.append(i)
                    visited[i] = True

            if remaining_bt[current] > 0:
                queue.append(current)

            if all(bt == 0 for bt in remaining_bt):
                break

        for i in range(n):
            turnaround_time[i] = completion_time[i] - arrival_time[i]
            waiting_time[i] = turnaround_time[i] - burst_time[i]

        return {
            "waiting_time": waiting_time,
            "turnaround_time": turnaround_time,
            "completion_time": completion_time
        }

    def priority_scheduling(self, processes):
        for process in processes:
            process['waiting_time'] = 0
            process['turnaround_time'] = process['burstTime']
            process['response_time'] = 0

        avg_wt = sum(p['waiting_time'] for p in processes) / len(processes)
        avg_tat = sum(p['turnaround_time'] for p in processes) / len(processes)
        avg_rt = sum(p['response_time'] for p in processes) / len(processes)

        return {
            "processes": processes,
            "avg_wt": avg_wt,
            "avg_tat": avg_tat,
            "avg_rt": avg_rt
        }

    def fcfs(self, processes):
        if not processes:
            return {"error": "Missing processes."}

        if not all(['arrival_time' in p and 'burst_time' in p for p in processes]):
            return {"error": "Each process must have 'arrival_time' and 'burst_time'."}

        processes.sort(key=lambda x: int(x['arrival_time']))
        current_time = 0

        for process in processes:
            arrival_time = int(process['arrival_time'])
            burst_time = int(process['burst_time'])
            current_time = max(current_time, arrival_time) + burst_time
            process['completion_time'] = current_time
            process['turnaround_time'] = process['completion_time'] - arrival_time
            process['waiting_time'] = process['turnaround_time'] - burst_time

        total_waiting_time = sum(process['waiting_time'] for process in processes)
        total_turnaround_time = sum(process['turnaround_time'] for process in processes)
        total_response_time = total_waiting_time

        avg_waiting_time = total_waiting_time / len(processes)
        avg_turnaround_time = total_turnaround_time / len(processes)
        avg_response_time = total_response_time / len(processes)

        return {
            "waiting_time": [p['waiting_time'] for p in processes],
            "turnaround_time": [p['turnaround_time'] for p in processes],
            "response_time": [p['waiting_time'] for p in processes],
            "avg_wt": avg_waiting_time,
            "avg_tat": avg_turnaround_time,
            "avg_rt": avg_response_time
        }

    def preemptive_sjf(self, process_list):
        if not process_list:
            return {"error": "Missing processes."}

        if not all(['arrival' in p and 'burst' in p for p in process_list]):
            return {"error": "Each process must have 'arrival' and 'burst'."}

        process_list.sort(key=lambda x: x['arrival'])
        processes = []
        for pid, process in enumerate(process_list, start=1):
            processes.append({
                "pid": pid,
                "arrival": process['arrival'],
                "burst": process['burst'],
                "remaining": process['burst'],
                "completion": 0,
                "waiting": 0,
                "turnaround": 0,
                "response": -1,
            })

        time = 0
        completed = 0
        ready_queue = []

        while completed < len(processes):
            for process in processes:
                if process["arrival"] <= time and process["remaining"] > 0 and process not in ready_queue:
                    ready_queue.append(process)

            if ready_queue:
                ready_queue.sort(key=lambda x: x["remaining"])
                current_process = ready_queue[0]

                if current_process["response"] == -1:
                    current_process["response"] = time - current_process["arrival"]

                current_process["remaining"] -= 1
                time += 1

                if current_process["remaining"] == 0:
                    current_process["completion"] = time
                    current_process["turnaround"] = current_process["completion"] - current_process["arrival"]
                    current_process["waiting"] = current_process["turnaround"] - current_process["burst"]
                    ready_queue.remove(current_process)
                    completed += 1
            else:
                time += 1

        total_waiting = sum(process["waiting"] for process in processes)
        total_turnaround = sum(process["turnaround"] for process in processes)
        total_response = sum(process["response"] for process in processes)
        avg_waiting = total_waiting / len(processes)
        avg_turnaround = total_turnaround / len(processes)
        avg_response = total_response / len(processes)

        return {
            "processes": processes,
            "avg_wt": avg_waiting,
            "avg_tat": avg_turnaround,
            "avg_rt": avg_response
        }

    def sjf_non_preemptive(self, processes):
        if not processes:
            return {"error": "Missing processes."}

        if not all(['arrival_time' in p and 'burst_time' in p for p in processes]):
            return {"error": "Each process must have 'arrival_time' and 'burst_time'."}

        n = len(processes)
        time = 0
        completed = 0
        processes.sort(key=lambda x: (x['arrival_time'], x['burst_time']))
        executed = [False] * n
        gantt_chart = []

        while completed < n:
            shortest = None
            for i in range(n):
                if not executed[i] and processes[i]['arrival_time'] <= time:
                    if shortest is None or processes[i]['burst_time'] < processes[shortest]['burst_time']:
                        shortest = i

            if shortest is not None:
                process = processes[shortest]
                gantt_chart.append((process['pid'], time, time + process['burst_time']))
                time += process['burst_time']
                process['completion_time'] = time
                process['turnaround_time'] = process['completion_time'] - process['arrival_time']
                process['waiting_time'] = process['turnaround_time'] - process['burst_time']
                process['response_time'] = time - process['burst_time'] - process['arrival_time']
                executed[shortest] = True
                completed += 1
            else:
                time += 1

        waiting_times = [p['waiting_time'] for p in processes]
        turnaround_times = [p['turnaround_time'] for p in processes]
        response_times = [p['response_time'] for p in processes]

        return {
            "processes": processes,
            "gantt_chart": gantt_chart,
            "avg_wt": sum(waiting_times) / n,
            "avg_tat": sum(turnaround_times) / n,
            "avg_rt": sum(response_times) / n,
        }

@app.route('/priority_scheduling', methods=['POST'])
def priority_scheduling():
    data = request.get_json()
    processes = data.get("processes")

    if processes:
        scheduler = CPUScheduling()
        result = scheduler.priority_scheduling(processes)
        return jsonify(result)
    return jsonify({"error": "Missing processes."}), 400

@app.route('/round_robin', methods=['POST'])
def round_robin():
    data = request.get_json()
    scheduling = CPUScheduling()
    result = scheduling.round_robin(data)
    return jsonify(result)

@app.route('/fcfs', methods=['POST'])
def fcfs():
    data = request.get_json()
    processes = data.get("processes")
    scheduler = CPUScheduling()
    result = scheduler.fcfs(processes)
    return jsonify(result)

@app.route('/preemptive_sjf', methods=['POST'])
def preemptive_sjf():
    data = request.get_json()
    processes = data.get("processes")
    scheduler = CPUScheduling()
    result = scheduler.preemptive_sjf(processes)
    return jsonify(result)

@app.route('/sjf_non_preemptive', methods=['POST'])
def sjf_non_preemptive():
    data = request.get_json()
    cpu_scheduler = CPUScheduling()
    result = cpu_scheduler.sjf_non_preemptive(data['processes'])
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
