<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>

/* ===== GLOBAL ===== */
body {
    font-family: Arial, sans-serif;
    background-color: #f4f7f6;
    margin: 0;
    padding: 10px; /* Prevent blank first page */
    -webkit-print-color-adjust: exact;
}

/* ===== HEADER ===== */
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 15px;
    padding: 0 20px;
}

.logo-left{
    float:left
}
.logo-right {
    float:right
}

.logo-left img,
.logo-right img {
    height: 80px;
    max-width: 100%;
}

.center-content {
    flex: 1;
    text-align: center;
}

.title-box {
    background: #0b6b3a;
    color: white;
    font-size: 28px;
    font-weight: 800;
    border-radius: 12px;
    display: inline-block;
}

.date-box {
    display: inline-block;
    background: #f2f8f5;
    padding: 3px 20px;
    border-radius: 25px;
    color: #0b6b3a;
    font-size: 14px;
    font-weight: 600;
    border: 2px solid #1f6f3e;
    margin-top: 10px;
}

/* ===== TABLE LAYOUT (WKHTMLTOPDF SAFE) ===== */
table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 10px;
    table-layout: fixed;
    page-break-inside: auto;
}

tr {
    page-break-inside: auto;
}

td {
    vertical-align: top;
    page-break-inside: auto;
}

/* ===== CARDS ===== */
.card {
    background: white;
    border-radius: 12px;
    padding: 15px;
    box-sizing: border-box;
}

/* ===== SECTION HEADINGS ===== */
h3 {
    margin-top: 0;
    font-size: 18px;
    border-bottom: 2px solid #f0f0f0;
    padding-bottom: 8px;
    margin-bottom: 12px;
}

/* ===== NEWS ITEMS (AVOID BREAK INSIDE) ===== */
.news-item {
    margin-bottom: 12px;
    border-bottom: 1px solid #eee;
    padding-bottom: 8px;
    page-break-inside: avoid;
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
}

.news-title {
    font-weight: 700;
    color: #333;
    font-size: 14px;
    text-decoration: none;
    display: block;
}

.news-summary {
    font-size: 12px;
    color: #666;
    line-height: 1.4;
    margin: 5px 0;
}

.news-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.read-more {
    font-size: 11px;
    color: #0b6b3a;
    text-decoration: none;
    font-weight: bold;
}

.source {
    font-size: 10px;
    color: #999;
}

.no-news {
    color: #999;
    font-size: 12px;
}

/* ===== IMAGES ===== */
img {
    max-width: 100%;
    height: auto;
    display: block;
}

/* ===== FOOTER ===== */
.footer {
    text-align: center;
    margin-top: 30px;
    font-size: 13px;
    color: #1f6f3e;
}
.card {
    page-break-inside: avoid;
}

table {
    page-break-inside: auto;
}

tr {
    page-break-inside: avoid;
}
</style>
</head>
<body>

<table style="width:100%; margin-bottom:5px;">
  <tr>
    <td style="width:5%; text-align:left;">
      <img src="State_emblem_of_Pakistan.png" height="30">
    </td>
    <td style="width:60%; text-align:center;">
      <div style="font-size:28px; font-weight:800; color:#0b6b3a;">
        DAILY MEDIA ENERGY MONITOR
      </div>
      <div style="margin-top:8px; font-size:14px; font-weight:600; color:#1f6f3e;">
        {{REPORT_DATE}}
      </div>
    </td>
    <td style="width:5%; text-align:right;">
      <img src="MMS.png" height="30">
    </td>
  </tr>
</table>

<table style="
    width:100%;
    border-collapse:collapse;
    table-layout:fixed;
    border:1px solid #333;
">
    {{Logos}}
</table>
<table style="width:100%; ">
    <tr>
        <td style="width:50%; vertical-align:top; text-align:center;">
            {{Sentiment_piechart}}
        </td>

        <td style="width:50%; vertical-align:top; ">
            {{summary}}
        </td>
    </tr>
</table>
<div style="margin:20px 0;">

<!-- ================= MAIN 70 / 30 LAYOUT ================= -->

<table style="width:100%; border-spacing:20px;">

<tr>

<td style="width:100%; vertical-align:top;">

<!-- ================= NEWS ================= -->

<h2 style="color:#0b5e2e; border-bottom:2px solid #e6f4ec; padding-bottom:5px;">
Key Energy Topics
</h2>

<!-- ===== TOPICS GRID ===== -->

<table style="width:100%; border-spacing:15px;">

<tr>

<td style="background:#ffffff; padding:12px; border-top:5px solid #0b6b3a; border-radius:6px;">
<h3 style="color:#0b6b3a; margin-top:0;">Net Metering</h3>
<div style="font-size:13px;">{{NET_METERING}}</div>
</td>

<td style="background:#ffffff; padding:12px; border-top:5px solid #1f6f3e; border-radius:6px;">
<h3 style="color:#1f6f3e; margin-top:0;">Solarization</h3>
<div style="font-size:13px;">{{SOLARIZATION}}</div>
</td>

<td style="background:#ffffff; padding:12px; border-top:5px solid #2e7d4f; border-radius:6px;">
<h3 style="color:#2e7d4f; margin-top:0;">Privatisation</h3>
<div style="font-size:13px;">{{PRIVATISATION}}</div>
</td>

</tr>

<tr>

<td style="background:#ffffff; padding:12px; border-top:5px solid #0b6b3a; border-radius:6px;">
<h3 style="color:#0b6b3a; margin-top:0;">Tariff Hikes</h3>
<div style="font-size:13px;">{{TARIFF}}</div>
</td>

<td style="background:#ffffff; padding:12px; border-top:5px solid #1f6f3e; border-radius:6px;">
<h3 style="color:#1f6f3e; margin-top:0;">Fuel Price Adjustment</h3>
<div style="font-size:13px;">{{FUEL}}</div>
</td>

<td style="background:#ffffff; padding:12px; border-top:5px solid #1f6f3e; border-radius:6px;">
<h3 style="color:#d9534f; margin-top:0;">Load Shedding</h3>
<div style="font-size:13px;">{{LOAD}}</div>
</td>

</tr>

</table>

<br>

<!-- ================= MISC ================= -->

<table>
<tr>
<td class="card" style="border-top: 6px solid #0b6b3a;">
<h3 style="color:#0b6b3a;">Misc</h3>

{{OTHER}}

</td>
</tr>
</table>

<br>

<!-- ================= SOCIAL MEDIA ================= -->

<h2 style="color:#0b5e2e; border-bottom:2px solid #43a1df; padding-bottom:5px;">
Social Media Insights
</h2>

<table style="width:100%; border-spacing:10px;">

<tr>
<td style="background:#e6f4ec; padding:12px; border:1px solid #ddd; border-radius:6px;">

<table style="width:100%; border-collapse:collapse;">
<tr>

<td style="width:33%; vertical-align:top;">
{{Social_Media_1}}
</td>

<td style="width:33%; vertical-align:top;">
{{Social_Media_2}}
</td>

<td style="width:33%; vertical-align:top;">
{{Social_Media_3}}
</td>

</tr>
</table>

</td>
</tr>

</table>

</td>

</tr>

</table>
<div class="footer">
    
    <b>Advanced Data Analytics</b><br> <br>
    For Queries: power.post@ppmc.gov.pk
</div>

</body>
</html>