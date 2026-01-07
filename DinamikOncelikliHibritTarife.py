import time
import copy
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import random  # Veri üretimi için eklendi

# Dinamik Öncelikli Hibrit Tarife (MLFQ)
# Amaç: MLFQ, RR ve SRTF algoritmalarını karşılaştırarak performans analizi yapmak.


class Process:
    """
    İşletim sistemindeki bir 'Süreci' (Process) temsil eden sınıf.
    Her sürecin kimliği, geliş zamanı ve ihtiyaç duyduğu süre burada tutulur.
    """
    def __init__(self, pid, arrival_time, burst_time):
        self.pid = pid                  # Sürecin Kimlik Numarası (Örn: 1, 2, 3...)
        self.arrival_time = arrival_time # Sisteme kaçıncı saniyede girdiği
        self.burst_time = burst_time    # İşin tamamlanması için gereken toplam CPU süresi
        self.remaining_time = burst_time # Simülasyon anında geriye kalan iş süresi (Azalacak)
        
        # Performans Analizi İçin Tutulan İstatistikler
        self.start_time = -1            # CPU'yu ilk kez ne zaman aldı? (Tepki süresi için)
        self.completion_time = 0        # İş ne zaman tamamen bitti?
        self.wait_time = 0              # Kuyrukta işlemci beklerken geçirdiği toplam süre
        self.turnaround_time = 0        # (Bitiş Zamanı - Geliş Zamanı) toplam sistemde kalma süresi
        self.response_time = 0          # (İlk Başlama - Geliş Zamanı) ekrana ilk tepki süresi
        
        # MLFQ Algoritmasına Özel Sayaçlar
        self.total_executed = 0         # Bu süreç toplamda kaç saniye CPU kullandı? (Ceza kontrolü için)
        self.time_in_queue = 0          # Şu anki bulunduğu kuyrukta ne kadar süredir çalışıyor? (Quantum için)
        self.in_queue = False           # Kod tekrarı olmasın diye kuyrukta olup olmadığını takip eder

    def __repr__(self):
        # Çıktılarda nesne adresi yerine "P1", "P2" yazması için
        return f"P{self.pid}"

# GÖRSEL YARDIMCI: TERMİNAL TABLO TASARIMI
# Bu fonksiyonlar hesaplama yapmaz, sadece terminal çıktısının güzel görünmesini sağlar.
def print_dashboard_header(title):
    print("\n" + "╔" + "═"*95 + "╗") # Üst çerçeve
    print(f"║ {title:^93} ║")       # Başlığı ortala
    # Sütun başlıklarını ve ayırıcı çizgileri yazdır
    print("╠" + "═"*8 + "╦" + "═"*6 + "╦" + "═"*12 + "╦" + "═"*8 + "╦" + "═"*57 + "╣")
    print(f"║ {'ZAMAN':<6} ║ {'PID':<4} ║ {'KUYRUK':<10} ║ {'KALAN':<6} ║ {'İŞLEM / KARAR MEKANİZMASI':<55} ║")
    print("╠" + "═"*8 + "╬" + "═"*6 + "╬" + "═"*12 + "╬" + "═"*8 + "╬" + "═"*57 + "╣")

def print_dashboard_row(time, pid, queue, rem, detail):
    # Kuyruk ismini formatla (Yoksa tire koy)
    q_str = f"Q{queue}" if queue != "-" else "-"
    # Tek bir satır veriyi tablo formatında yazdır
    print(f"║ {time:<6} ║ P{pid:<3} ║ {q_str:<10} ║ {rem:<6} ║ {detail:<55} ║")

def print_dashboard_footer():
    # Tablonun alt çizgisini kapatmak için
    print("╚" + "═"*8 + "╩" + "═"*6 + "╩" + "═"*12 + "╩" + "═"*8 + "╩" + "═"*57 + "╝")


# SENARYO VERİLERİ (DATA GENERATOR)

def get_scenario_data(choice):
    """
    Kullanıcının seçtiği numaraya göre farklı test verileri döndürür.
    Amaç: Algoritmayı tek bir duruma göre değil, her ihtimale göre test etmektir.
    """
    data = []
    # Veri sayısını 1000'e çıkardık
    count = 1000 
    
    if choice == 1:
        # Karma Senaryo: Kısa, uzun ve orta işlerin karışık olduğu dengeli test.
        # 1000 veri için rastgele dağılım yapıyoruz.
        for i in range(1, count + 1):
            arrival = random.randint(0, 500) # Geliş zamanı dağınık
            burst = random.randint(1, 30)    # 1 ile 30 arası karışık süreler
            data.append((i, arrival, burst))
        return data, "Karma (Standart) Senaryo - 1000 Veri"
        
    elif choice == 2:
        # Etkileşimli Senaryo: Genelde kısa süren işler (Mouse hareketi, klavye girdisi gibi).
        # MLFQ burada çok başarılı olmalı.
        for i in range(1, count + 1):
            arrival = random.randint(0, 500)
            # %90 ihtimalle kısa iş (1-4 sn), %10 ihtimalle uzun iş
            if random.random() < 0.9:
                burst = random.randint(1, 4)
            else:
                burst = random.randint(10, 20)
            data.append((i, arrival, burst))
        return data, "Etkileşimli (Kısa İş) Senaryosu - 1000 Veri"
        
    elif choice == 3:
        # Ağır Yük Senaryosu: Tüm işler çok uzun. (Video render, bilimsel hesaplama).
        # MLFQ burada Round Robin'e dönüşmeli.
        for i in range(1, count + 1):
            arrival = random.randint(0, 200) # İşler hızlıca sisteme yağıyor
            burst = random.randint(15, 50)   # Hepsi uzun sürüyor (10sn üzeri)
            data.append((i, arrival, burst))
        return data, "Ağır Yük (CPU Bound) Senaryosu - 1000 Veri"
        
    elif choice == 4:
        # Stres Testi: Uzun bir iş çalışırken sürekli araya giren kısa işler (Kesinti/Preemption).
        # MLFQ'nun hızlı tepki yeteneğini ölçer.
        # İlk 10 iş çok uzun, geri kalan 990 iş çok kısa ve sık aralıklarla geliyor
        for i in range(1, 11):
            data.append((i, 0, 200)) # Çok uzun işler başta
        
        for i in range(11, count + 1):
            arrival = random.randint(1, 1000) # Sürekli geliyorlar
            burst = random.randint(1, 3)      # Çok kısalar
            data.append((i, arrival, burst))
            
        return data, "Stres ve Kesinti (Preemption) Testi - 1000 Veri"
        
    return [], "Bilinmeyen"


# ALGORİTMA 1: MLFQ (Multi-Level Feedback Queue)

def run_mlfq(processes, verbose=True):
    # Eğer detaylı mod (verbose) açıksa, tablo başlığını yazdır
    if verbose: print_dashboard_header("MLFQ SİMÜLASYONU (Dinamik Öncelik)")
    
    current_time = 0        # Simülasyon saati (0'dan başlar)
    completed = []          # Biten işlemleri buraya atacağız
    
    # 3 Seviyeli Kuyruk Yapısı Oluşturuluyor:
    q0 = deque() # En yüksek öncelik (Quantum = 2sn) - Yeni gelenler buraya
    q1 = deque() # Orta öncelik (Quantum = 4sn)
    q2 = deque() # En düşük öncelik (FCFS) - Uzun süre çalışanlar buraya düşer
    
    threshold_heavy = 10    # 10sn çalışan "ağır iş" sayılır

    # Tüm işlemler bitene kadar döngü devam eder
    while len(completed) < len(processes):
        
        # Sisteme yeni giren süreç var mı kontrol et
        for p in processes:
            if p.arrival_time == current_time: # Şu anki saniyede gelen iş var mı?
                q0.append(p)                   # Varsa en yüksek önceliğe (Q0) ekle
                if verbose: print_dashboard_row(current_time, p.pid, "0 (VIP)", p.remaining_time, "--> Sisteme giriş yaptı (Yüksek Öncelik).")

        # Hangi işi çalıştıracağız? (Öncelik kontrolü)
        active = None
        source_q = -1
        
        # Önce Q0'a bak, boşsa Q1'e, o da boşsa Q2'ye bak
        if q0: active = q0.popleft(); source_q = 0
        elif q1: active = q1.popleft(); source_q = 1
        elif q2: active = q2.popleft(); source_q = 2
        
        # Eğer çalıştırılacak bir iş bulunduysa:
        if active:
            # İşlemci ilk kez bu işi alıyorsa, "Response Time"ı kaydet
            if active.start_time == -1:
                active.start_time = current_time
                active.response_time = current_time - active.arrival_time

            # İşlemciyi 1 birim zaman çalıştır
            active.remaining_time -= 1      # Kalan iş süresini azalt
            active.total_executed += 1      # Toplam çalışma süresini artır
            active.time_in_queue += 1       # Bu kuyrukta harcadığı süreyi artır
            current_time += 1               # Zamanı ilerlet
            
            # İş bitti mi kontrolü
            if active.remaining_time == 0:
                # İstatistikleri hesapla
                active.completion_time = current_time
                active.turnaround_time = active.completion_time - active.arrival_time
                active.wait_time = active.turnaround_time - active.burst_time
                completed.append(active) # Bitenlere ekle
                if verbose: print_dashboard_row(current_time, active.pid, "Bitti", 0, "*** İşlem tamamlandı ve sistemden çıktı.")
            
            # İş bitmediyse kuralları uygula (Feedback Mekanizmamız)
            else:
                # 10 saniye kuralı
                # Eğer iş toplamda 10sn çalıştıysa ve henüz en altta değilse, en alta at.
                if active.total_executed >= threshold_heavy and source_q != 2:
                    if verbose: print_dashboard_row(current_time, active.pid, f"Q{source_q}->Q2", active.remaining_time, "CEZA: 10sn kotası doldu, en alta düşürüldü.")
                    active.time_in_queue = 0 # Yeni kuyruk için sayacı sıfırla
                    q2.append(active)        # Q2'ye sürgün et
                
                # Q0'daysa ve 2 saniyelik hakkını (Quantum) doldurduysa
                elif source_q == 0:
                    if active.time_in_queue >= 2:
                        if verbose: print_dashboard_row(current_time, active.pid, "Q0->Q1", active.remaining_time, "Süre (2sn) bitti, öncelik düşürüldü.")
                        active.time_in_queue = 0
                        q1.append(active)    # Bir alt kuyruğa (Q1) düşür
                    else:
                        q0.appendleft(active) # Süresi dolmadıysa, Q0'ın başına geri koy
                
                # Q1'deyse ve 4 saniyelik hakkını doldurduysa
                elif source_q == 1:
                    if active.time_in_queue >= 4:
                        if verbose: print_dashboard_row(current_time, active.pid, "Q1->Q2", active.remaining_time, "Süre (4sn) bitti, Q2'ye aktarıldı.")
                        active.time_in_queue = 0
                        q2.append(active)    # En alt kuyruğa (Q2) düşür
                    else:
                        q1.appendleft(active) # Süresi dolmadıysa devam et
                
                # Q2'deyse (Round Robin / FCFS mantığı)
                elif source_q == 2:
                    q2.appendleft(active)    # Kesilmediği sürece çalışmaya devam etsin
        
        else:
            # Hiçbir kuyrukta iş yoksa işlemci boştadır
            if verbose: print_dashboard_row(current_time, "-", "-", "-", "CPU Boşta...")
            current_time += 1
            
    if verbose: print_dashboard_footer()
    return completed

# ALGORİTMA 2: ROUND ROBIN (RR)

def run_rr(processes, quantum=4, verbose=True):
    if verbose: print_dashboard_header(f"ROUND ROBIN SİMÜLASYONU (Sabit Quantum={quantum})")
    
    current_time = 0
    completed = []
    queue = deque()       # Tek bir kuyruk var
    p_in_queue = set()    # Hangi process kuyrukta, tekrar eklememek için takip listesi
    processes.sort(key=lambda x: x.arrival_time) # Geliş sırasına göre diz

    while len(completed) < len(processes):
        # Yeni gelenleri kuyruğa ekle
        for p in processes:
            # Eğer zamanı geldiyse VE kuyrukta değilse VE bitmediyse
            if p.arrival_time <= current_time and p.pid not in p_in_queue and p not in completed:
                queue.append(p)
                p_in_queue.add(p.pid)
                if verbose: print_dashboard_row(current_time, p.pid, "Kuyruk", p.remaining_time, "Sıraya girdi.")

        if queue:
            p = queue.popleft() # Kuyruğun başındakini al
            
            # İlk kez çalışıyorsa başlangıç zamanını kaydet
            if p.start_time == -1:
                p.start_time = current_time
                p.response_time = current_time - p.arrival_time

            # Quantum süresi kadar veya iş bitene kadar döngü kur
            exec_time = 0
            while exec_time < quantum and p.remaining_time > 0:
                p.remaining_time -= 1
                current_time += 1
                exec_time += 1
                
                # İşlemci çalışırken o arada yeni bir iş gelirse onu kuyruğa almalıyız
                for new_p in processes:
                    if new_p.arrival_time == current_time and new_p.pid not in p_in_queue and new_p not in completed:
                        queue.append(new_p)
                        p_in_queue.add(new_p.pid)
                        if verbose: print_dashboard_row(current_time, new_p.pid, "Kuyruk", new_p.remaining_time, "Yeni işlem geldi, sıranın sonuna eklendi.")

            # Döngüden çıkınca kontrol et iş bitti mi?
            if p.remaining_time == 0:
                p.completion_time = current_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.wait_time = p.turnaround_time - p.burst_time
                completed.append(p)
                if verbose: print_dashboard_row(current_time, p.pid, "Bitti", 0, "*** İşlem tamamlandı.")
            else:
                # Bitmediyse kuyruğun sonuna geri at
                queue.append(p)
                if verbose: print_dashboard_row(current_time, p.pid, "Kuyruk", p.remaining_time, "Quantum doldu, sıranın sonuna atıldı.")
        else:
            # Kuyruk boşsa bekle
            if verbose: print_dashboard_row(current_time, "-", "-", "-", "CPU Boşta")
            current_time += 1
            
    if verbose: print_dashboard_footer()
    return completed


# ALGORİTMA 3: SRTF (Shortest Remaining Time First) - Benchmark

def run_srtf(processes, verbose=True):
    if verbose: print_dashboard_header("SRTF (TEORİK REFERANS) SİMÜLASYONU")
    
    current_time = 0
    completed = []
    last_pid = -1 # Context switch (işlem değişimi) olup olmadığını anlamak için
    
    while len(completed) < len(processes):
        # O an gelmiş ve henüz bitmemiş olan tüm işleri bul
        available = [p for p in processes if p.arrival_time <= current_time and p.remaining_time > 0]
        
        if available:
            # Kalan süresi en az olanı seç (SRTF Mantığı)
            shortest = min(available, key=lambda x: x.remaining_time)
            
            # İlk başlama zamanı kaydı
            if shortest.start_time == -1:
                shortest.start_time = current_time
                shortest.response_time = current_time - shortest.arrival_time
            
            # Eğer işlemci başka bir işten bu işe geçtiyse log yaz
            if shortest.pid != last_pid:
                if verbose: print_dashboard_row(current_time, shortest.pid, "CPU", shortest.remaining_time, "!! En kısa kalan iş olduğu için CPU'yu kaptı.")
                last_pid = shortest.pid
                
            # 1 birim çalıştır
            shortest.remaining_time -= 1
            current_time += 1
            
            # Bitti mi?
            if shortest.remaining_time == 0:
                shortest.completion_time = current_time
                shortest.turnaround_time = shortest.completion_time - shortest.arrival_time
                shortest.wait_time = shortest.turnaround_time - shortest.burst_time
                completed.append(shortest)
                if verbose: print_dashboard_row(current_time, shortest.pid, "Bitti", 0, "*** İşlem tamamlandı.")
                last_pid = -1
        else:
            if verbose: print_dashboard_row(current_time, "-", "-", "-", "CPU Boşta")
            current_time += 1
            
    if verbose: print_dashboard_footer()
    return completed

# DETAYLI ANALİZ MODÜLÜM

def analyze_detailed(mlfq_res, rr_res, srtf_res, scenario_name):
    # Başlık Yazdırma
    print("\n")
    print("┏" + "━"*90 + "┓")
    print(f"┃ {'PERFORMANS ANALİZ VE SONUÇ RAPORU: ' + scenario_name:^88} ┃")
    print("┗" + "━"*90 + "┛")
    
    # Verileri PID sırasına diz (Karşılaştırmamız doğru olsun diye)
    mlfq_res.sort(key=lambda x: x.pid)
    rr_res.sort(key=lambda x: x.pid)
    srtf_res.sort(key=lambda x: x.pid)

    # 1. İşleri Kategorize Et (Kısa vs Uzun)
    # Burst Time 5'ten küçükse "Kısa", 10'dan büyükse "Uzun" kabul et
    short_jobs = [p.pid for p in mlfq_res if p.burst_time <= 5]
    long_jobs = [p.pid for p in mlfq_res if p.burst_time > 10]
    
    # Ortalama Hesaplama Yardımcı Fonksiyonu
    def calc_avg(res, pids=None):
        subset = res if pids is None else [p for p in res if p.pid in pids]
        if not subset: return 0.0 # Eğer o kategoride iş yoksa 0 döndür
        return sum(p.wait_time for p in subset) / len(subset)

    # İstatistikleri Çıkar
    m_avg = calc_avg(mlfq_res); r_avg = calc_avg(rr_res); s_avg = calc_avg(srtf_res)
    m_short = calc_avg(mlfq_res, short_jobs); r_short = calc_avg(rr_res, short_jobs); s_short = calc_avg(srtf_res, short_jobs)
    m_long = calc_avg(mlfq_res, long_jobs); r_long = calc_avg(rr_res, long_jobs)
    
    # Response Time (Screen Time) Ortalamaları
    m_resp = sum(p.response_time for p in mlfq_res) / len(mlfq_res)
    r_resp = sum(p.response_time for p in rr_res) / len(rr_res)
    s_resp = sum(p.response_time for p in srtf_res) / len(srtf_res)

    # DİNAMİK YORUM MANTIĞI (Rakamlara Göre Cümle Kurma) 
    
    # Kısa İşler Performansı
    if r_short > 0:
        gain_short = ((r_short - m_short) / r_short * 100) # İyileşme yüzdesi
    else: gain_short = 0
    
    if gain_short > 0:
        perf_comment = f"MLFQ, kısa işleri tespit edip önceliklendirerek Round Robin'e göre %{gain_short:.1f} daha hızlı tamamlamıştır."
    elif gain_short == 0:
        perf_comment = "Bu senaryoda iş yükü dağılımı sebebiyle her iki algoritma da kısa işlerde benzer (Eşit) performans göstermiştir."
    else:
        perf_comment = f"Bu senaryoda Round Robin, MLFQ'ya göre daha iyi sonuç vermiştir (Nadir durum)."

    # Screen Time (Tepki Süresi) Performansı
    if r_resp > 0:
        gain_resp = ((r_resp - m_resp) / r_resp * 100)
    else: gain_resp = 0
    
    if gain_resp > 0:
        resp_comment = f"MLFQ, kullanıcı deneyimini (Screen Time) %{gain_resp:.1f} oranında iyileştirmiştir."
    else:
        resp_comment = "Tepki süresi her iki algoritmada da benzer seviyededir."

    # Trade-off Analizi (Uzun İşler Zarar Gördü mü?)
    if long_jobs:
        loss_long = m_long - r_long
        trade_comment = f"Kısa işlere yer açmak için, uzun işler MLFQ'da ortalama {loss_long:.2f} ms daha fazla beklemiştir (Trade-off)."
    else:
        trade_comment = "Senaryoda çok uzun süreli iş bulunmadığı için negatif bir ödünleşim (trade-off) oluşmamıştır."

    # ANALİZ TABLOSUNU YAZDIRMA
    print(f"{'METRİK':<35} | {'MLFQ (Önerilen)':<18} | {'RR (Standart)':<18} | {'SRTF (Referans)':<15}")
    print("-" * 92)
    # Ortalamalar
    print(f"{'Ortalama Bekleme (ms)':<35} | {m_avg:<18.2f} | {r_avg:<18.2f} | {s_avg:<15.2f}")
    # Kısa İşler Detayı
    print(f"{'Kısa İşler Bekleme (ms)':<35} | {m_short:<18.2f} | {r_short:<18.2f} | {s_short:<15.2f}")
    # Uzun İşler Detayı (Varsa yaz, yoksa tire koy)
    if long_jobs:
        print(f"{'Uzun İşler Bekleme (ms)':<35} | {m_long:<18.2f} | {r_long:<18.2f} | {'-':<15}")
    # Screen Time Detayı
    print(f"{'Tepki Süresi / Screen Time (ms)':<35} | {m_resp:<18.2f} | {r_resp:<18.2f} | {s_resp:<15.2f}")
    print("-" * 92)

    # SÖZEL DEĞERLENDİRMEMİZ
    print("\n>>> SİMÜLASYON DEĞERLENDİRMESİ")
    print(f"1. PERFORMANS: {perf_comment}")
    print(f"2. DENEYİM: {resp_comment}")
    print(f"3. TRADE-OFF: {trade_comment}")
    print(f"4. BENCHMARK: Geliştirilen algoritma, teorik limit olan SRTF'ye {abs(m_avg - s_avg):.2f} ms yaklaşmıştır.")
    
    # Grafik iste
    ask_graph([mlfq_res, rr_res, srtf_res], scenario_name)


# BENCHMARK MODU (TÜM SENARYOLAR)
# Bu fonksiyonumuzda tüm senaryoları sırayla çalıştırıp özet bir karne çıkartırız.

def compare_all_benchmarks():
    print("\n" + "░"*90)
    print(f"{'GENEL KARŞILAŞTIRMA (BENCHMARK SUITE - 1000 Veri)':^90}")
    print("░"*90 + "\n")
    print("NOT: 1000 veri işleniyor, lütfen bekleyin...\n")
    
    results = []
    # 4 Senaryoyu döngü ile çalıştır
    for i in range(1, 5):
        raw, name = get_scenario_data(i)
        # Veri kopyalama
        d1=[Process(p,a,b) for p,a,b in raw]; d2=copy.deepcopy(d1); d3=copy.deepcopy(d1)
        # Sessiz modda (False) çalıştır, sadece sonuç al
        r1=run_mlfq(d1, False); r2=run_rr(d2, 4, False)
        # Ortalamaları hesapla
        w1 = sum(p.wait_time for p in r1)/len(r1); w2 = sum(p.wait_time for p in r2)/len(r2)
        results.append((name, w1, w2))
        print(f">> {name} simülasyonu tamamlandı.")

    # Özet Tablom
    print("\n" + "═"*90)
    print(f"{'SENARYO TİPİ':<45} | {'MLFQ (Wait)':<15} | {'RR (Wait)':<15} | {'DURUM'}")
    print("-" * 90)
    for name, m, r in results:
        diff = ((r - m) / r * 100) if r > 0 else 0
        # Kazananı belirle
        if m < r: status = f"MLFQ %{diff:.0f} Hızlı"
        elif r < m: status = f"RR %{abs(diff):.0f} Hızlı"
        else: status = "EŞİT (0 Fark)"
        print(f"{name:<45} | {m:<15.2f} | {r:<15.2f} | {status}")
    print("═"*90)

    print("\n>>> GENEL SONUÇ:")
    print("Bu tablo, MLFQ algoritmasının 'adapte olabilir' yapısını kanıtlar.")
    print("- Kısa/Etkileşimli işlerde Q0 kuyruğu sayesinde büyük fark atar.")
    print("- Ağır işlerde Q2 kuyruğuna düşerek Round Robin gibi davranır ve sistemi korur.")

    ask_graph_summary(results)


# GRAFİK ÇİZİM FONKSİYONLARI (Matplotlib)

def ask_graph(results, title):
    """
    1000 veri için optimize edilmiş Hız ve Kararlılık grafikleri.
    Düzenleme: Alt açıklama metni grafikten ayrıldı, etiketler düzeltildi.
    """
    if input("\nGrafikleri görüntülemek için 'E' tuşuna basın: ").lower() == 'e':
        m_list, r_list, s_list = results
        
        # Grafik stili
        plt.style.use('ggplot')
        fig, ax = plt.subplots(1, 2, figsize=(16, 8)) # Yüksekliği biraz artırdım (7 -> 8)
        
        # ---------------------------------------------------------
        # GRAFİK 1: GENEL HIZ KARŞILAŞTIRMASI (BAR CHART)
        # ---------------------------------------------------------
        
        metrics = ['Ortalama Bekleme\n(Wait Time)', 'Ortalama Tepki\n(Response Time)', 'Ort. Sistemde Kalma\n(Turnaround)']
        
        def get_means(lst):
            avg_wait = sum(p.wait_time for p in lst) / len(lst)
            avg_resp = sum(p.response_time for p in lst) / len(lst)
            avg_turn = sum(p.turnaround_time for p in lst) / len(lst)
            return [avg_wait, avg_resp, avg_turn]

        m_means = get_means(m_list)
        r_means = get_means(r_list)
        s_means = get_means(s_list)
        
        x = np.arange(len(metrics))
        width = 0.25

        # DÜZELTME 1: Etiket ismi güncellendi
        rects1 = ax[0].bar(x - width, m_means, width, label='MLFQ (Önerilen)', color='#27ae60')
        rects2 = ax[0].bar(x, r_means, width, label='Round Robin (Standart)', color='#c0392b')
        rects3 = ax[0].bar(x + width, s_means, width, label='SRTF (Teorik Limit)', color='#7f8c8d', alpha=0.6)

        ax[0].set_ylabel('Süre (Milisaniye)')
        ax[0].set_title(f'{title}\nGENEL PERFORMANS ÖZETİ', fontweight='bold', fontsize=11)
        ax[0].set_xticks(x)
        ax[0].set_xticklabels(metrics)
        ax[0].legend()
        
        # Sütun üstüne değer yazma
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax[0].annotate(f'{height:.0f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        autolabel(rects1)
        autolabel(rects2)

        # ---------------------------------------------------------
        # GRAFİK 2: KARARLILIK ANALİZİ (BOX PLOT)
        # ---------------------------------------------------------
        
        data_to_plot = [
            [p.wait_time for p in m_list],
            [p.wait_time for p in r_list],
            [p.wait_time for p in s_list]
        ]
        
        bp = ax[1].boxplot(data_to_plot, patch_artist=True, labels=['MLFQ', 'Round Robin', 'SRTF'])
        
        colors = ['#2ecc71', '#e74c3c', '#95a5a6']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
            
        ax[1].set_title(f'{title}\nKARARLILIK ANALİZİ (Bekleme Süresi Dağılımı)', fontweight='bold', fontsize=11)
        ax[1].set_ylabel('Bekleme Süresi (ms)')
        ax[1].grid(True, linestyle='--', alpha=0.5)
        
        # ---------------------------------------------------------
        # AÇIKLAMA METNİ VE AYARLAMALAR
        # ---------------------------------------------------------
        
        stats_text = (
            "GRAFİK OKUMA KILAVUZU:\n"
            "► SOL GRAFİK (HIZ): Sütunlar ne kadar kısaysa o kadar iyidir (Daha az bekleme).\n"
            "► SAĞ GRAFİK (KARARLILIK): Kutu ne kadar aşağıda ve kısaysa, algoritma o kadar istikrarlıdır.\n"
            "   (Kutunun içindeki çizgi ortalama değeri gösterir.)"
        )
        
        # Yazıyı ortala ve hafif yukarı al
        plt.figtext(0.5, 0.02, stats_text, ha="center", fontsize=10, 
                    bbox={"facecolor":"orange", "alpha":0.1, "pad":8})

        # DÜZELTME 2: Alt boşluğu (bottom) 0.15 yaparak yazının grafiğe girmesini engelledik.
        plt.tight_layout(rect=[0, 0.15, 1, 1]) 
        plt.show()

def ask_graph_summary(results):
    if input("\nÖzet grafiği görüntülemek için 'E' tuşuna basın: ").lower() == 'e':
        labels = [x[0].split(' ')[0] for x in results]
        x = np.arange(len(labels)); w = 0.35
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x-w/2, [x[1] for x in results], w, label='MLFQ', color='green')
        ax.bar(x+w/2, [x[2] for x in results], w, label='RR', color='blue')
        ax.set_title("Tüm Senaryoların Karşılaştırması (1000 Veri)"); ax.set_xticks(x); ax.set_xticklabels(labels); ax.legend()
        plt.show()

# MENÜ

if __name__ == "__main__":
    while True:
        print("\n" + "█"*60)
        print(f"{'SÜREÇ ÇİZELGELEME TEST LABORATUVARI (1000 Veri)':^60}")
        print("█"*60)
        print("1. Standart Senaryo (Dengeli)")
        print("2. Etkileşimli Senaryo (Kısa İşler)")
        print("3. Ağır Yük Senaryosu (Uzun İşler)")
        print("4. Stres Testi (Sık Kesinti)")
        print("5. GENEL BENCHMARK (Tümünü Kıyasla)")
        print("0. Çıkış")
        
        try:
            choice = int(input("\nSeçiminiz: "))
            if choice == 0: break
            if choice == 5: compare_all_benchmarks()
            elif 1 <= choice <= 4:
                raw, name = get_scenario_data(choice)
                
                # 1000 veri için log uyarısı
                print(f"\n[SİSTEM UYARISI] {len(raw)} adet veri işlenecek.")
                print("Detaylı logları açmak terminali yavaşlatabilir.")
                v_inp = input("Detaylı logları (Her adımı) görmek ister misiniz? (E/H): ").lower()
                is_verbose = True if v_inp == 'e' else False
                
                # Her algoritma için temiz veri kopyası oluştur
                d1=[Process(p,a,b) for p,a,b in raw]; d2=copy.deepcopy(d1); d3=copy.deepcopy(d1)
                
                # Algoritmaları çalıştır
                r1=run_mlfq(d1, is_verbose); r2=run_rr(d2, 4, is_verbose); r3=run_srtf(d3, is_verbose)
                
                # Sonuçları analiz et
                analyze_detailed(r1, r2, r3, name)
            else: print("Geçersiz seçim.")
            input("\nDevam etmek için Enter...")
        except ValueError: print("Lütfen sayı giriniz.")