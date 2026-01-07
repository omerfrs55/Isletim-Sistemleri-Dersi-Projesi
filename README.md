
# BÜYÜK ÖLÇEKLİ VERİ SETLERİ VE SÜPERMARKET KASA SİMÜLASYONU İLE DİNAMİK MLFQ ÇİZELGELEME ALGORİTMASININ PERFORMANS ANALİZİ

## 1. Proje ve Ders Bilgileri

Bu çalışma, Piri Reis Üniversitesi, Denizcilik Meslek Yüksekokulu, Bilgisayar Teknolojileri Bölümü müfredatında yer alan İşletim Sistemleri dersi kapsamında, final projesi olarak geliştirilmiştir.

* **Ders Kodu ve Adı:** BIP 2027 - İŞLETİM SİSTEMLERİ
* **Akademik Dönem:** 2025-2026 Güz
* **Dersi Veren Öğretim Görevlisi:** Refik Tanju SİRMEN
* **Öğrenci Adı Soyadı:** Ömer Faruk SAĞLAM
* **Öğrenci Numarası:** 20230108011
* **Teslim Tarihi:** 07.01.2026

---

## 2. Proje Özeti ve Amacı

Merkezi İşlem Birimi (CPU) kaynaklarının verimli yönetimi, modern işletim sistemlerinde performansın temel belirleyicisidir. Geleneksel çizelgeleme algoritmaları (Round Robin vb.), değişken iş yükleri altında adalet ve yanıt süresi dengesini sağlamakta zorlanabilmektedir.

Bu projede, süreç davranışlarını modellemek için **"Süpermarket Kasa Yönetimi"** analojisi kullanılmış ve **"10 Saniye Eşik Kuralı"** ile optimize edilmiş dinamik bir **Çok Seviyeli Geri Beslemeli Kuyruk (MLFQ)** algoritması geliştirilmiştir.

**Temel Amaçlar:**
1.  Kısa süreli (etkileşimli) işlerin bekleme süresini minimize etmek (Ekspres Kasa mantığı).
2.  Uzun süreli (işlemci yoğun) işlerin sistemi tıkamasını (starvation) önlemek.
3.  Round Robin (RR) ve teorik En Kısa Kalan İş Öncelikli (SRTF) algoritmaları ile kıyaslamalı performans analizi yapmak.

---

## 3. Materyal ve Yöntem

Simülasyon, Python programlama dili kullanılarak Nesne Yönelimli Programlama (OOP) prensiplerine uygun olarak geliştirilmiştir. Veri yapıları için `collections.deque` kullanılarak kuyruk işlemleri O(1) zaman karmaşıklığında gerçekleştirilmiştir.

### 3.1. Algoritma Mimarisi (Kuyruk Hiyerarşisi)
Geliştirilen Dinamik MLFQ algoritması, üç seviyeli bir yapıdan oluşmaktadır:

* **Q0 - Yüksek Öncelik (Ekspres Kasa):**
    * **Zaman Kuantumu:** 2 Saniye.
    * **İşlevi:** Sisteme yeni giren işler buraya alınır. Kısa süreli işler anında tamamlanır.
* **Q1 - Orta Öncelik (Normal Kasa):**
    * **Zaman Kuantumu:** 4 Saniye.
    * **İşlevi:** Q0'da tamamlanamayan orta ölçekli işler buraya aktarılır.
* **Q2 - Düşük Öncelik (Toptan Kasa):**
    * **Yöntem:** FCFS (İlk Gelen İlk Hizmet Görür).
    * **İşlevi:** Uzun süreli işlemci yoğunluklu işler burada işlenir.

### 3.2. Özgün Yaklaşım: 10 Saniye Ceza Kuralı (Threshold Rule)
Bu çalışmanın literatüre sunduğu temel katkı **"10 Saniye Kuralı"**dır. Simülasyon, her sürecin kümülatif çalışma süresini takip eder. Toplam işlemci kullanım süresi **10 saniyeyi aşan** herhangi bir süreç, hangi kuyrukta olduğuna bakılmaksızın "İşlemci Oburu" (CPU-Bound) olarak etiketlenir ve doğrudan en alt kuyruğa (Q2) taşınır. Bu mekanizma, sistemin tıkanmasını (Head-of-Line Blocking) engeller.

---

## 4. Test Senaryoları (Büyük Veri Yaklaşımı)

Algoritmaların performansı, her biri **1.000 adet rastgele süreçten** oluşan dört farklı stres senaryosu altında test edilmiştir:

1.  **Senaryo 1: Standart Gün (Karma Yük):** Süreçlerin %33'ü kısa, %33'ü orta ve %33'ü uzun işlerden oluşur. Dengeli bir sistem yükünü temsil eder.
2.  **Senaryo 2: Ekspres Kasa Yoğunluğu (Etkileşimli):** Süreçlerin %90'ı 1-4 saniyelik çok kısa işlerdir (I/O yoğunluklu sistemler).
3.  **Senaryo 3: Toptancı Akını (Ağır Yük):** Tüm süreçlerin 15-60 saniye aralığında olduğu, işlemci yoğunluklu senaryodur.
4.  **Senaryo 4: Kaos ve Müdahale (Stres Testi):** Sistemde uzun işler çalışırken, sürekli olarak (990 adet) çok kısa ve acil işlerin araya girdiği (preemption) senaryodur.

---

## 5. Bulgular ve Performans Sonuçları

Aşağıdaki tablo, 1.000 verilik benchmark testleri sonucunda elde edilen ortalama bekleme sürelerini (milisaniye cinsinden) göstermektedir:

| Senaryo Tipi | MLFQ Ort. Bekleme (ms) | RR Ort. Bekleme (ms) | Performans Farkı | Sonuç Değerlendirmesi |
| :--- | :--- | :--- | :--- | :--- |
| **1. Standart Gün** | **8507.20** | 9649.68 | **MLFQ %12 Daha İyi** | Dengeli yüklerde MLFQ, dinamik önceliklendirme ile belirgin avantaj sağlamıştır. |
| **2. Ekspres Kasa** | 1540.75 | **1373.20** | RR %12 Daha İyi | Çok kısa işlerde MLFQ'nun kuyruk yönetim maliyeti (overhead), performans kaybına yol açmıştır. |
| **3. Ağır Yük** | **19074.53** | 25920.69 | **MLFQ %26 Daha İyi** | "10 Saniye Kuralı" uzun işleri izole ederek sistemin tıkanmasını engellemiştir. En yüksek verim burada alınmıştır. |
| **4. Kaos (Stres)** | 725.46 | **681.43** | RR %6 Daha İyi | Sık kesme (context switch) gerektiren durumlarda Round Robin daha kararlı çalışmıştır. |

---

## 6. Kurulum ve Çalıştırma

Projenin kaynak kodlarını yerel ortamınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz.

### Gereksinimler
* Python 3.10 veya üzeri
* Gerekli kütüphaneler: `matplotlib`, `numpy`

### Kurulum Adımları
Terminal veya komut satırında proje dizinine giderek gerekli kütüphaneleri yükleyiniz:

pip install matplotlib numpy

```

### Simülasyonu Başlatma

Ana uygulama dosyasını çalıştırarak simülasyon menüsüne erişebilirsiniz:

python main.py

```

*(Not: Dosya ismi projedeki ana çalıştırılabilir dosyaya göre değişiklik gösterebilir.)*


## 7. Sonuç
Bu çalışma, "tek bir en iyi algoritma olmadığını", performansın iş yükü karakteristiğine göre değiştiğini kanıtlamıştır. Geliştirilen Dinamik MLFQ algoritması, özellikle karmaşık ve ağır yüklerde (Senaryo 1 ve 3) Round Robin'e göre **%12 ile %26 arasında** performans artışı sağlamıştır. Ancak çok kısa ve yoğun işlerde, algoritmanın yönetim maliyeti (overhead) nedeniyle basit döngüsel yaklaşımların (RR) daha verimli olabileceği gözlemlenmiştir.

"10 Saniye Ceza Eşiği" mekanizmasının, işlemci yoğunluklu süreçlerin sistemi domine etmesini engellemede başarılı olduğu ve sistem kararlılığını artırdığı sonucuna varılmıştır.

