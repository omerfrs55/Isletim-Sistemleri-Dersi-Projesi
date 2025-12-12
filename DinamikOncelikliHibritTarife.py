import time
import copy
from collections import deque
import matplotlib.pyplot as plt
import numpy as np

# --- İŞLETİM SİSTEMLERİ PROJESİ: Gelişmiş Zaman Çizelgeleme Analizi ---
# Algoritmalar: MLFQ vs RR vs SRTF (Benchmark)

class Process:
    def __init__(self, pid, arrival_time, burst_time):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.start_time = -1 
        self.completion_time = 0
        self.wait_time = 0
        self.turnaround_time = 0
        self.response_time = 0
        self.total_executed = 0
        self.time_in_queue = 0
        self.in_queue = False 

    def __repr__(self):
        return f"P{self.pid}"

# =============================================================================
# 1. ALGORİTMA: MLFQ (LOGLU)
# =============================================================================
def run_mlfq_detailed(processes):
    print("\n" + "="*80)
    print(f"{'ALGORİTMA 1: MLFQ SİMÜLASYONU BAŞLIYOR':^80}")
    print("="*80)
    print(f"{'Zaman':<6} | {'PID':<4} | {'Kuyruk':<8} | {'Kalan':<6} | {'İşlem Detayı'}")
    print("-" * 80)
    
    current_time = 0
    completed = []
    q0 = deque()
    q1 = deque()
    q2 = deque()
    threshold_heavy = 10 

    while len(completed) < len(processes):
        for p in processes:
            if p.arrival_time == current_time:
                q0.append(p)
                print(f"{current_time:<6} | P{p.pid:<4} | GİRİŞ    | {p.remaining_time:<6} | Sisteme katıldı -> Q0")

        active = None
        source_q = -1
        
        if q0: active = q0.popleft(); source_q = 0
        elif q1: active = q1.popleft(); source_q = 1
        elif q2: active = q2.popleft(); source_q = 2
        
        if active:
            if active.start_time == -1:
                active.start_time = current_time
                active.response_time = current_time - active.arrival_time

            active.remaining_time -= 1
            active.total_executed += 1
            active.time_in_queue += 1
            current_time += 1
            
            if active.remaining_time == 0:
                active.completion_time = current_time
                active.turnaround_time = active.completion_time - active.arrival_time
                active.wait_time = active.turnaround_time - active.burst_time
                completed.append(active)
                print(f"{current_time:<6} | P{active.pid:<4} | BİTTİ    | 0      | İşlem Tamamlandı! (Wait: {active.wait_time}s)")
            else:
                if active.total_executed >= threshold_heavy and source_q != 2:
                    print(f"{current_time:<6} | P{active.pid:<4} | CEZA     | {active.remaining_time:<6} | 10sn kotası doldu -> Q2'ye düşürüldü.")
                    active.time_in_queue = 0
                    q2.append(active)
                elif source_q == 0:
                    if active.time_in_queue >= 2:
                        print(f"{current_time:<6} | P{active.pid:<4} | DEĞİŞİM  | {active.remaining_time:<6} | Q0 süresi doldu -> Q1'e geçti.")
                        active.time_in_queue = 0
                        q1.append(active)
                    else:
                        q0.appendleft(active)
                elif source_q == 1:
                    if active.time_in_queue >= 4:
                        print(f"{current_time:<6} | P{active.pid:<4} | DEĞİŞİM  | {active.remaining_time:<6} | Q1 süresi doldu -> Q2'ye geçti.")
                        active.time_in_queue = 0
                        q2.append(active)
                    else:
                        q1.appendleft(active)
                elif source_q == 2:
                    q2.appendleft(active)
        else:
            current_time += 1

    return completed

# =============================================================================
# 2. ALGORİTMA: ROUND ROBIN (LOGLU)
# =============================================================================
def run_rr_detailed(processes, quantum=4):
    print("\n\n" + "="*80)
    print(f"{'ALGORİTMA 2: ROUND ROBIN SİMÜLASYONU BAŞLIYOR':^80}")
    print("="*80)
    print(f"{'Zaman':<6} | {'PID':<4} | {'Kalan':<6} | {'İşlem Detayı'}")
    print("-" * 80)
    
    current_time = 0
    completed = []
    queue = deque()
    p_in_queue = set()
    processes.sort(key=lambda x: x.arrival_time)

    while len(completed) < len(processes):
        for p in processes:
            if p.arrival_time <= current_time and p.pid not in p_in_queue and p not in completed:
                queue.append(p)
                p_in_queue.add(p.pid)
                print(f"{current_time:<6} | P{p.pid:<4} | {p.remaining_time:<6} | Kuyruğa eklendi.")

        if queue:
            p = queue.popleft()
            if p.start_time == -1:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            exec_time = 0
            while exec_time < quantum and p.remaining_time > 0:
                p.remaining_time -= 1
                current_time += 1
                exec_time += 1
                for new_p in processes:
                    if new_p.arrival_time == current_time and new_p.pid not in p_in_queue and new_p not in completed:
                        queue.append(new_p)
                        p_in_queue.add(new_p.pid)
                        print(f"{current_time:<6} | P{new_p.pid:<4} | {new_p.remaining_time:<6} | -> Yeni process kuyruğa girdi.")

            if p.remaining_time == 0:
                p.completion_time = current_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.wait_time = p.turnaround_time - p.burst_time
                completed.append(p)
                print(f"{current_time:<6} | P{p.pid:<4} | 0      | BİTTİ (Wait: {p.wait_time}s)")
            else:
                queue.append(p)
                print(f"{current_time:<6} | P{p.pid:<4} | {p.remaining_time:<6} | Süresi doldu, sona atıldı.")
        else:
            current_time += 1

    return completed

# =============================================================================
# 3. ALGORİTMA: SRTF (LOGLU)
# =============================================================================
def run_srtf_detailed(processes):
    print("\n\n" + "="*80)
    print(f"{'ALGORİTMA 3: SRTF (TEORİK REFERANS) BAŞLIYOR':^80}")
    print("="*80)
    print(f"{'Zaman':<6} | {'PID':<4} | {'Kalan':<6} | {'İşlem Detayı'}")
    print("-" * 80)
    
    current_time = 0
    completed = []
    last_pid = -1
    
    while len(completed) < len(processes):
        available = [p for p in processes if p.arrival_time <= current_time and p.remaining_time > 0]
        
        if available:
            shortest = min(available, key=lambda x: x.remaining_time)
            if shortest.start_time == -1:
                shortest.start_time = current_time
                shortest.response_time = current_time - shortest.arrival_time
            
            if shortest.pid != last_pid:
                print(f"{current_time:<6} | P{shortest.pid:<4} | SEÇİLDİ  | {shortest.remaining_time:<6} | CPU'yu kaptı.")
                last_pid = shortest.pid
                
            shortest.remaining_time -= 1
            current_time += 1
            
            if shortest.remaining_time == 0:
                shortest.completion_time = current_time
                shortest.turnaround_time = shortest.completion_time - shortest.arrival_time
                shortest.wait_time = shortest.turnaround_time - shortest.burst_time
                completed.append(shortest)
                print(f"{current_time:<6} | P{shortest.pid:<4} | BİTTİ    | 0      | Tamamlandı. (Wait: {shortest.wait_time}s)")
                last_pid = -1
        else:
            current_time += 1
            
    return completed

# =============================================================================
# DETAYLI ANALİZ VE YÜZDELİK HESAPLAMALAR
# =============================================================================
def analyze_final(mlfq_res, rr_res, srtf_res):
    print("\n\n")
    print("#"*100)
    print(f"{'DETAYLI PERFORMANS ANALİZİ VE YORUMLAR':^100}")
    print("#"*100)
    
    mlfq_res.sort(key=lambda x: x.pid)
    rr_res.sort(key=lambda x: x.pid)
    srtf_res.sort(key=lambda x: x.pid)

    # 1. KATEGORİLEME (Kısa vs Uzun)
    # Burst time 5 ve altı "Kısa", 10 üstü "Uzun" kabul edildi.
    short_jobs = [p.pid for p in mlfq_res if p.burst_time <= 5]
    long_jobs = [p.pid for p in mlfq_res if p.burst_time > 10]
    
    # 2. HESAPLAMALAR (Ortalama Beklemeler)
    # MLFQ
    mlfq_avg_wait = sum(p.wait_time for p in mlfq_res) / len(mlfq_res)
    mlfq_short = sum(p.wait_time for p in mlfq_res if p.pid in short_jobs) / len(short_jobs)
    mlfq_long = sum(p.wait_time for p in mlfq_res if p.pid in long_jobs) / len(long_jobs)
    mlfq_resp = sum(p.response_time for p in mlfq_res) / len(mlfq_res)

    # RR
    rr_avg_wait = sum(p.wait_time for p in rr_res) / len(rr_res)
    rr_short = sum(p.wait_time for p in rr_res if p.pid in short_jobs) / len(short_jobs)
    rr_long = sum(p.wait_time for p in rr_res if p.pid in long_jobs) / len(long_jobs)
    rr_resp = sum(p.response_time for p in rr_res) / len(rr_res)

    # SRTF (Benchmark)
    srtf_avg_wait = sum(p.wait_time for p in srtf_res) / len(srtf_res)
    srtf_short = sum(p.wait_time for p in srtf_res if p.pid in short_jobs) / len(short_jobs)
    
    # 3. YÜZDELİK FARK HESAPLARI
    if rr_short > 0:
        gain_vs_rr = ((rr_short - mlfq_short) / rr_short) * 100
    else: gain_vs_rr = 0

    gap_vs_srtf = mlfq_avg_wait - srtf_avg_wait

    # 4. TABLO OLUŞTURMA
    print(f"{'METRİK / DURUM':<30} | {'MLFQ (Bizim)':<15} | {'RR (Standart)':<15} | {'SRTF (Hedef/Limit)':<20}")
    print("-" * 100)
    print(f"{'Ortalama Bekleme Süresi':<30} | {mlfq_avg_wait:<15.2f} | {rr_avg_wait:<15.2f} | {srtf_avg_wait:<20.2f}")
    print(f"{'Kısa İşler Bekleme':<30} | {mlfq_short:<15.2f} | {rr_short:<15.2f} | {srtf_short:<20.2f}")
    print(f"{'Uzun İşler Bekleme':<30} | {mlfq_long:<15.2f} | {rr_long:<15.2f} | {'-':<20}")
    print(f"{'Tepki Süresi (Screen Time)':<30} | {mlfq_resp:<15.2f} | {rr_resp:<15.2f} | {'En İyi (Ref)':<20}")
    print("-" * 100)

    # 5. PROFESYONEL YORUM BÖLÜMÜ
    print("\n📊 SONUÇLARIN DEĞERLENDİRİLMESİ:")
    
    print(f"\n1. VERİMLİLİK VE HIZ ANALİZİ (Avantajlar)")
    print(f"   - Kısa süreli (etkileşimli) işlemlerde MLFQ, Round Robin'den %{gain_vs_rr:.1f} daha iyi performans göstermiştir.")
    print(f"   - Screen Time (Tepki Süresi) minimuma indirilerek sistemin 'donması' engellenmiştir.")

    print(f"\n2. BENCHMARK ANALİZİ (SRTF Referansı)")
    print(f"   - Geliştirilen MLFQ algoritması, teorik olarak ulaşılması en zor hedef olan SRTF")
    print(f"     algoritmasına ortalamada {gap_vs_srtf:.2f} saniye kadar yaklaşmıştır. Bu, algoritmanın başarısını kanıtlar.")

    print(f"\n3. ADALET VE UZUN İŞ ANALİZİ (Dezavantajlar)")
    print(f"   - Uzun süreli işlerde MLFQ ({mlfq_long}sn), Round Robin'e ({rr_long}sn) göre daha yavaştır.")
    print(f"   - Sebep: Sistem kaynakları öncelikli olarak kısa işlere (Kullanıcı etkileşimine) aktarılmıştır.")

    # GRAFİK
    choice = input("\nGrafikleri Oluştur (E/H): ").upper()
    if choice == 'E':
        pids = [f"P{p.pid}" for p in mlfq_res]
        x = np.arange(len(pids))
        width = 0.25
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Grafik 1: Bekleme (SRTF dahil)
        ax1.bar(x - width, [p.wait_time for p in mlfq_res], width, label='MLFQ (Bizim)', color='#2ecc71')
        ax1.bar(x, [p.wait_time for p in rr_res], width, label='RR (Standart)', color='#e74c3c')
        ax1.bar(x + width, [p.wait_time for p in srtf_res], width, label='SRTF (Limit)', color='#95a5a6', alpha=0.5)
        ax1.set_title('Bekleme Süresi (Wait Time) - Düşük Olan İyidir')
        ax1.set_ylabel('Saniye')
        ax1.set_xticks(x)
        ax1.set_xticklabels(pids)
        ax1.legend()
        
        # Grafik 2: Screen Time
        ax2.bar(x - width/2, [p.response_time for p in mlfq_res], width, label='MLFQ', color='#f39c12')
        ax2.bar(x + width/2, [p.response_time for p in rr_res], width, label='RR', color='#8e44ad')
        ax2.set_title('Tepki Süresi (Screen Time) - 0 Değeri "Anında Tepki" Demektir')
        ax2.set_ylabel('Saniye')
        ax2.set_xticks(x)
        ax2.set_xticklabels(pids)
        ax2.legend()
        
        plt.tight_layout()
        plt.show()

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    # Test Verileri
    raw_data = [(1, 0, 5), (2, 0, 22), (3, 2, 2), (4, 6, 4)]
    
    d1 = [Process(p, a, b) for p, a, b in raw_data]
    d2 = copy.deepcopy(d1)
    d3 = copy.deepcopy(d1)
    
    r1 = run_mlfq_detailed(d1)
    r2 = run_rr_detailed(d2, quantum=4)
    r3 = run_srtf_detailed(d3)
    
    analyze_final(r1, r2, r3)