# ULP Toolkit (cPanel / Plesk / WordPress)

Bu depo, büyük bir `ulp.txt` listesinden cPanel, Plesk ve WordPress ile ilgili satırları ayırmak, formatlamak ve cPanel/Plesk giriş denemelerini otomatikleştirmek için Python script'leri içerir.

## Icerik

- `filter_cpanel.py`: `ulp.txt` icinden cPanel/WHM satirlarini ayirir.
- `filter_plesk.py`: `ulp.txt` icinden Plesk satirlarini ayirir.
- `filter_wordpress.py`: `ulp.txt` icinden WordPress satirlarini ayirir.
- `format_cpanel_piped.py`: cPanel listelerini `https://host:port|user|pass` formatina cevirir.
- `format_plesk_piped.py`: Plesk listelerini `http(s)://host:port|user|pass` formatina cevirir.
- `cpanel.py`: cPanel giris denemesi yapar ve basarili satirlari kaydeder.
- `plesk.py`: Plesk giris denemesi yapar ve basarili satirlari kaydeder.

## Gereksinimler

- Python 3.10+
- Paketler:
  - `requests`
  - `colorama`
  - `termcolor`

Kurulum:

```bash
pip install requests colorama termcolor
```

## Girdi Formati

Script'ler satir bazli metin dosyalari ile calisir.

- Genel kaynak dosya: `ulp.txt`
- Ornek satirlar:
  - `https://example.com:2083|username|password`
  - `example.com:8443:username:password`
  - `example.com/smb/:username:password`

> Not: Bazi script'ler `|` ayracli, bazilari `:` ayracli satirlari da parse eder.

## Hizli Kullanim

### 1) Filtreleme

```bash
python filter_cpanel.py -i ulp.txt -o ulp_cpanel.txt
python filter_plesk.py -i ulp.txt -o ulp_plesk.txt
python filter_wordpress.py -i ulp.txt -o ulp_wordpress.txt
```

### 2) Format Donusumu

```bash
python format_cpanel_piped.py -i ulp_cpanel.txt -o ulp_cpanel_piped.txt
python format_plesk_piped.py -i ulp_plesk.txt -o ulp_plesk_piped.txt
```

### 3) Giris Kontrolu

```bash
python cpanel.py -f ulp_cpanel_piped.txt --threads 10 -o cpanel_success.txt
python plesk.py -f ulp_plesk_piped.txt --threads 10 -o plesk_success.txt
```

## Parametreler (Ozet)

- `-i`, `--input`: girdi dosyasi
- `-o`, `--output`: cikti dosyasi
- `-f`, `--file`: checker scriptlerinde girdi dosyasi
- `--threads`: eszamanli is parcacigi sayisi
- `--progress-every`: her N satirda ilerleme bilgisi
- `--append` (`plesk.py`): cikti dosyasina ekleme modu

## Ornek Akis

1. `ulp.txt` dosyasini filtrele (`filter_*`).
2. Sonucu standart formata cevir (`format_*_piped.py`).
3. Checker scripti ile giris dogrulama yap (`cpanel.py` / `plesk.py`).
4. Basarili satirlari `*_success.txt` dosyasindan incele.

## Uyari ve Sorumluluk

Bu araclari sadece yasal ve acik izniniz olan sistemlerde kullanin. Izinsiz erisim denemeleri yasal sorumluluk dogurur.

## Lisans

Bu depoda acik bir lisans dosyasi bulunmuyorsa, varsayilan olarak tum haklar saklidir. Acik kaynak lisanslamak icin bir `LICENSE` dosyasi eklemeniz onerilir.

