# Field Report: Metadata Analysis for OSINT

**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Interest Area:** Human investigation tactics / OSINT methodology
**Topic Slug:** metadata-analysis-osint
**Cross-Reference:** email-forensics-header-analysis, reverse-image-search-visual-osint, phone-number-osint, domain-whois-dns-investigation, data-breach-analysis-identity-linkage, social-media-osint-investigation-techniques
**Sources:** isosecu.com, spyboy.blog, exiftool.org

---

## 1. What I Explored

Metadata analysis as an OSINT discipline: the extraction, interpretation, and operational use of hidden file-level metadata (EXIF, XMP, PDF/DOCX document properties) for identity investigation, entity resolution, and timeline reconstruction. I dove into ExifTool (the canonical tool), built a Python-based extractor architecture (Pillow + PyPDF2 + python-docx), and mapped real-world forensic cases where metadata broke key investigations.

## 2. What I Found

### ExifTool — The Swiss Army Knife (2026 State)
- **Latest version:** ExifTool 13.xx (early 2026), still maintained by Phil Harvey
- **Supported formats:** hundreds — images, video, audio, PDF, Office docs
- **Core capabilities:** read/write/strip metadata, GPS extraction, makernote parsing, steganography detection
- **Real-world impact cases:** BTK Killer (MS Word metadata -> "Dennis" + church name), Bellingcat (timestamp manipulation in conflict videos), dark-web vendor geolocation via product photos
- **Critical CVE:** CVE-2021-22204 — command injection via crafted DjVu/JPEG, exploited in the wild against GitLab and other apps that used ExifTool for metadata sanitization

### Image Metadata (EXIF) as OSINT Gold
- GPSLatitude/Longitude -> precise location (within meters)
- DateTimeOriginal, DateTimeDigitized -> timeline anchor points
- Make, Model, Software -> device fingerprinting and correlation
- UserComment, ImageDescription -> potential hidden payloads (base64, scripts)
- Common leaks: 80%+ of social media photos from personal devices still carry some EXIF

### PDF Metadata Forensics
- /Author, /Creator, /Producer, /CreationDate, /ModDate
- Real case: ransomware note PDFs with Chinese-language metadata exposed false "American" attribution
- Common red flags: old/cracked Adobe versions, mismatched author/location
- PDFs retain editing chain metadata (xmpMM:History) — track who opened/modified a document

### Office Document Metadata (DOCX, XLSX, PPTX)
- python-docx accessible: Author, Created, Modified, LastModifiedBy, Title, Revision
- Corporate espionage: employees leak internal usernames and software versions via metadata on shared documents
- FOCA (Fingerprinting Organizations with Collected Archives) automates bulk metadata extraction from public-facing documents

### DIY Python Extractor Architecture
Built from spyboy.blog's blueprint:
- Image EXIF extraction via Pillow `_getexif()` with TAGS mapping
- PDF metadata via PyPDF2 `PdfReader.metadata`
- DOCX properties via python-docx `Document.core_properties`
- JSON output with structured key-value pairs
- Extensible to: video metadata (ffmpeg/ffprobe), audio ID3 tags, archive comment fields

## 3. What I Think Is Interesting

**The BTK metadata breakthrough is the canonical case study.** A serial killer evaded capture for 31 years, then sent a floppy disk. Police asked the church if they used MS Word; metadata said "Dennis" was the author. That single metadata field collapsed the investigation. The lesson: metadata is a side channel that people don't know they're broadcasting.

**Metadata analysis is fundamentally a temporal alignment problem.** EXIF timestamps, PDF modification chains, and document revision histories all encode temporal signals. Combine these with email Received headers, domain WHOIS dates, and social media posting times -> you can reconstruct a person's digital timeline with forensic precision.

**The ExifTool CVE illustrates the double-edged nature.** ExifTool is both the primary defensive tool (stripping metadata before sharing) and itself a high-value attack surface. Defenders who use it without updating are opening a hole. The tool is so ubiquitous that a single RCE in it cascades across GitLab, ImageMagick pipelines, and countless security products.

**There's a tool gap between FOCA (automated but Windows-only, GUI) and ExifTool (powerful but CLI/POSIX).** A multi-format, cross-platform metadata aggregation tool that normalizes output to a common schema and integrates with Exocortex's entity resolution pipeline is missing from the open-source landscape. This is a buildable capability.

## 4. What I'd Explore Next

1. **FOCA deep-dive:** Architecture, metadata normalization patterns, automated document scraping + metadata extraction pipeline
2. **Video/audio metadata forensics:** ffmpeg/ffprobe for container/codec metadata, digital video watermarking detection, audio spectrogram steganography
3. **Metadata correlation engine:** Given N files from different sources, how do you cluster them by common metadata fingerprints (same camera serial, same author, same timestamps)? This is entity resolution applied to file artifacts.
4. **Privacy-preserving metadata sanitization strategies:** What should a journalist/anonymous source SOP look like? Which fields must be stripped, and which stripping methods leave forensic residue?

## 5. Cross-Domain Connections

- **Email header analysis:** Both extract hidden sender/device metadata from object wrappers — email headers from SMTP, EXIF from image containers. Same pattern: the wrapper tells you more than the content.
- **Entity resolution:** Metadata fields (camera serial number, author name, PDF Producer string) are entity attributes that can be used for deconfliction and linkage across files from different sources.
- **Reverse image search:** EXIF GPS can validate or contradict visual geolocation claims. Combining visual landmarks + GPS metadata is stronger than either alone.
- **Counterintelligence analysis:** Adversaries can plant deceptive metadata (timestamp manipulation, forged GPS). Metadata veracity assessment requires the same source reliability weighting frameworks as HUMINT reporting.
- **Data breach analysis:** Breached databases often include hashed passwords stored alongside metadata-rich documents. Correlating document author fields with usernames in breaches can de-anonymize accounts.

---

**Key Insight:** Metadata is not about the file — it's about the creator's operational fingerprint. Every EXIF tag, PDF author field, and Word revision log is a silent witness to the environment, tools, and timeline of the person who produced the file. Master metadata, and you can read the digital exhaust that people don't realize they're leaving.
