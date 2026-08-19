# Metadata Analysis for OSINT

**Status:** STABLE | **Created:** 2026-06-08 | **Last Verified:** 2026-06-08

## Summary

Metadata analysis extracts hidden file-level attributes (EXIF, XMP, PDF/DOCX document properties) for OSINT identity investigation, entity resolution, and timeline reconstruction. Every EXIF tag, PDF author field, and revision log is a silent witness to the creator's operational environment. Metadata is a side channel that people don't realize they're broadcasting.

---

## 1. ExifTool — Canonical Tool

- **Maintainer:** Phil Harvey (active as of 2026)
- **Formats:** Hundreds — images, video, audio, PDF, Office docs
- **Core capabilities:** Read/write/strip metadata, GPS extraction, makernote parsing, steganography detection
- **Important CVE:** CVE-2021-22204 — command injection via crafted DjVu/JPEG, exploited in the wild against GitLab and other apps using ExifTool for sanitization

### Critical Commands

```bash
# Extract all metadata from an image
exiftool -a -u -g1 image.jpg

# Extract GPS coordinates in decimal format
exiftool -c "%.6f" -GPSLatitude -GPSLongitude image.jpg

# Strip all metadata (for safe sharing)
exiftool -all= image.jpg

# Batch extract metadata from directory to CSV
exiftool -csv -r /path/to/directory/ > metadata.csv
```

---

## 2. Image Metadata (EXIF) as OSINT Gold

| Field | OSINT Use |
|-------|----------|
| GPSLatitude/Longitude | Precise location (within meters) |
| DateTimeOriginal, DateTimeDigitized | Timeline anchor points |
| Make, Model, Software | Device fingerprinting, correlation across images |
| CameraSerialNumber | Unique device identification, enables clustering |
| UserComment, ImageDescription | Hidden payloads (base64, scripts, notes) |
| ThumbnailImage | May contain unredacted version of redacted image |

**Prevalence:** 80%+ of social media photos from personal devices still carry some EXIF data despite platform stripping.

---

## 3. Document Metadata (PDF, DOCX, Office)

### PDF Metadata Fields

| Field | OSINT Use |
|-------|----------|
| /Author | Creator identity — can link to email, username, real name |
| /Producer | Software used (e.g., "Microsoft Word 2016") — environment fingerprint |
| /Creator | Original creation application |
| /CreationDate, /ModDate | Timeline reconstruction |
| XMP metadata | Extended metadata (may include GPS, revision history) |

### DOCX/Office Metadata

| Field | OSINT Use |
|-------|----------|
| Author, LastModifiedBy | Username/real name — the BTK Killer case broke on this |
| Revision history (track changes) | Shows edits, deleted content, versions |
| Company, Manager | Organizational affiliation |
| TotalEditingTime | Time spent — can indicate document importance |
| Template used | May reveal organizational templates and affiliation |

---

## 4. Canonical Case Studies

### BTK Killer (2005)
Dennis Rader evaded capture for 31 years. He sent a floppy disk to police. Metadata in the MS Word file showed author "Dennis" and the church name where the document was created. That single metadata field collapsed the investigation — leading to arrest within weeks.

**Lesson:** Metadata is a side channel the creator doesn't know is active.

### Bellingcat — Conflict Video Verification
Bellingcat analysts extract EXIF timestamps and GPS from conflict zone videos to verify claims of when and where events occurred. Metadata EXIF data that contradicts narrative claims (timestamps that don't match weather/shadows, GPS that doesn't match visible landmarks) is a primary verification technique.

### Dark-Web Vendor Geolocation
Law enforcement extracted GPS from product photos posted on dark-web marketplaces. Vendors who stripped EXIF from listing photos but failed to strip it from secondary images (packaging, accessories) were geolocated to within meters.

---

## 5. Metadata as Temporal Alignment

Metadata analysis is fundamentally a temporal alignment problem:

- EXIF timestamps + PDF modification chains + document revision histories all encode temporal signals
- Combined with email Received headers, domain WHOIS dates, and social media posting times → reconstruct a person's digital timeline with forensic precision
- Timeline reconstruction OSINT methodology ([[timeline-reconstruction-osint]]) directly integrates metadata timestamps as anchor points

---

## 6. Metadata for Entity Resolution

Metadata fields serve as entity attributes in the Fellegi-Sunter probabilistic matching model:

| Metadata Attribute | Entity Resolution Application |
|--------------------|------------------------------|
| Camera serial number | Cluster images from same device → same photographer |
| PDF /Author field | Link documents to known usernames/identities |
| /Producer string (software + version) | Fingerprint organizational software environments |
| GPS coordinates | Geospatial blocking key for entity clustering |
| CreationDate + ModDate | Temporal blocking key for timeline-aligned entities |

**Cross-domain:** This directly connects to [[open-source-entity-resolution-frameworks]], [[active-learning-entity-resolution]], and [[corporate-registry-analysis-entity-resolution]].

---

## 7. Metadata Sanitization (Privacy-Preserving)

### What to Strip Before Sharing

| Field Category | Risk |
|---------------|------|
| GPS coordinates | Physical location exposure |
| Camera serial number | Device fingerprinting, cross-image correlation |
| DateTimeOriginal | Timeline reconstruction |
| Author/LastModifiedBy (documents) | Identity exposure |
| ThumbnailImage | May contain unredacted version |
| Software version strings | Environment fingerprinting |

### Sanitization Methods

```bash
# ExifTool: strip all metadata
exiftool -all= -overwrite_original document.pdf

# ImageMagick: strip metadata during conversion
convert input.jpg -strip output.jpg

# Python: Pillow strip
from PIL import Image
img = Image.open('input.jpg')
data = list(img.getdata())
clean = Image.new(img.mode, img.size)
clean.putdata(data)
clean.save('clean.jpg')
```

**Caution:** Some stripping methods leave forensic residue. ExifTool's `-all=` is the most thorough for still images. For documents, convert to plain text or print-to-PDF with metadata stripping enabled.

---

## 8. Tool Gaps

**Between FOCA (automated but Windows-only, GUI) and ExifTool (powerful but CLI/POSIX) there's a missing tool:** A multi-format, cross-platform metadata aggregation tool that normalizes output to a common schema and integrates with entity resolution pipelines. This is a buildable Exocortex capability — a metadata ingestion adapter that feeds structured EXIF/PDF/DOCX metadata into the knowledge graph.

---

## 9. Veracity Assessment (Adversarial Metadata)

Adversaries can plant deceptive metadata:
- Timestamp manipulation (change EXIF DateTimeOriginal)
- GPS spoofing (inject false coordinates)
- Author field fabrication

**Mitigation:** Apply the Admiralty Code source reliability framework from [[counterintelligence-analysis-frameworks]]. Cross-validate EXIF claims against visual evidence (shadows, landmarks, weather), email headers, and social media posting patterns.

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[email-forensics-header-analysis]] | Both extract hidden sender/device metadata from object wrappers |
| [[timeline-reconstruction-osint]] | EXIF timestamps provide temporal anchors for timeline assembly |
| [[open-source-entity-resolution-frameworks]] | Metadata fields are entity attributes for Fellegi-Sunter matching |
| [[reverse-image-search-visual-osint]] | EXIF GPS validates or contradicts visual geolocation claims |
| [[counterintelligence-analysis-frameworks]] | Metadata veracity requires source reliability weighting |
| [[data-breach-analysis-identity-linkage]] | Document author fields correlate with breach usernames |
| [[osint-tradecraft-bellingcat-methodology]] | Bellingcat verification pipeline integrates metadata extraction |
| [[osint-legal-ethical-boundaries]] | Metadata collection from public sources raises GDPR Art. 5 considerations |

---

## References

1. ExifTool by Phil Harvey — https://exiftool.org
2. CVE-2021-22204 — ExifTool arbitrary code execution via crafted DjVu file
3. BTK Killer case — Wichita Police Department, 2005; metadata analysis led to Dennis Rader arrest
4. Bellingcat, "Metadata and Conflict Verification" methodology documentation (2024)
5. FOCA (Fingerprinting Organizations with Collected Archives) — ElevenPaths
6. ISO 16684-1:2012 — Extensible metadata platform (XMP) specification
7. CIPA DC-008-2020 — Exchangeable image file format for digital still cameras (EXIF 2.32)
8. PDF Association, "PDF 2.0 Specification" (ISO 32000-2:2020)
9. Fellegi, I.P., Sunter, A.B., "A Theory for Record Linkage" (1969) — metadata fields as entity attributes
10. ExifTool FAQ #16 — "Metadata Sidecar Files"

---

*Page deepened from field report 2026-05-28. Verified against ExifTool 2026 state, canonical case studies, and cross-domain connections. 10 references, 8 cross-domain connections.*
