/**
 * ملف JavaScript لوظائف الطباعة والتصدير لصفحات المعمل
 */

// دالة تصدير إلى PDF
function exportToPDF(title, direction = 'rtl') {
    // إخفاء أزرار الطباعة والتصدير مؤقتًا
    const printButtons = document.querySelector('.print-buttons');
    if (printButtons) {
        printButtons.style.display = 'none';
    }

    const { jsPDF } = window.jspdf;

    // تحديد اتجاه الصفحة بناءً على عرض الجدول
    const tableWidth = document.querySelector('table').offsetWidth;
    const orientation = tableWidth > 500 ? 'landscape' : 'portrait';

    // إنشاء PDF
    const doc = new jsPDF({
        orientation: orientation,
        unit: 'mm',
        format: 'a4',
        compress: true,
        putOnlyUsedFonts: true,
        direction: 'rtl'
    });

    // إضافة دعم للغة العربية
    doc.setFont('Tajawal');
    doc.setR2L(true); // دائمًا من اليمين إلى اليسار

    // الحصول على محتوى الصفحة
    const content = document.querySelector('.print-container');

    // استخدام html2canvas لتحويل المحتوى إلى صورة
    html2canvas(content, {
        scale: 2,
        useCORS: true,
        logging: false,
        allowTaint: true
    }).then(canvas => {
        // إضافة الصورة إلى PDF
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = doc.internal.pageSize.getWidth() - 20;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        // إضافة العنوان
        doc.setFontSize(16);
        doc.text(title, doc.internal.pageSize.getWidth() / 2, 10, { align: 'center' });

        // إضافة الصورة
        doc.addImage(imgData, 'PNG', 10, 20, imgWidth, imgHeight);

        // إضافة ترقيم الصفحات
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(10);
            doc.text(`صفحة ${i} من ${pageCount}`, doc.internal.pageSize.getWidth() / 2, doc.internal.pageSize.getHeight() - 10, { align: 'center' });
        }

        // تنزيل الملف
        const filename = `${title.replace(/ /g, '_')}_${new Date().toISOString().slice(0, 10)}.pdf`;
        doc.save(filename);

        // إظهار الأزرار مرة أخرى
        if (printButtons) {
            printButtons.style.display = 'block';
        }
    });
}

// دالة تصدير إلى Excel
function exportToExcel(title) {
    // الحصول على جدول البيانات
    const table = document.querySelector('table');

    if (!table) {
        console.error('لم يتم العثور على جدول في الصفحة');
        alert('لم يتم العثور على جدول في الصفحة');
        return;
    }

    try {
        // إنشاء مصفوفة لتخزين البيانات
        const data = [];

        // إضافة العناوين
        const headers = [];
        const headerCells = table.querySelectorAll('thead th');
        headerCells.forEach(cell => {
            headers.push(cell.innerText.trim());
        });

        // عكس ترتيب العناوين للحصول على الترتيب الصحيح من اليمين إلى اليسار
        headers.reverse();
        data.push(headers);

        // إضافة البيانات
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const rowData = [];
            const cells = row.querySelectorAll('td');

            // تحويل NodeList إلى مصفوفة وعكس ترتيبها
            const cellsArray = Array.from(cells);
            cellsArray.reverse();

            cellsArray.forEach(cell => {
                rowData.push(cell.innerText.trim());
            });

            data.push(rowData);
        });

        // إنشاء ورقة عمل
        const ws = XLSX.utils.aoa_to_sheet(data);

        // تعيين اتجاه الخلايا من اليمين إلى اليسار
        ws['!rtl'] = true;

        // تعيين عرض الأعمدة
        const colWidth = [];
        headers.forEach(() => {
            colWidth.push({ wch: 20 }); // عرض كل عمود 20 وحدة
        });
        ws['!cols'] = colWidth;

        // إنشاء مصنف عمل
        const wb = XLSX.utils.book_new();
        // تعيين خصائص المصنف
        wb.Workbook = {
            Views: [{ RTL: true }] // تعيين اتجاه الورقة من اليمين إلى اليسار
        };
        XLSX.utils.book_append_sheet(wb, ws, 'البيانات');

        // تنزيل الملف
        const filename = `${title.replace(/ /g, '_')}_${new Date().toISOString().slice(0, 10)}.xlsx`;
        XLSX.writeFile(wb, filename);
    } catch (error) {
        console.error('حدث خطأ أثناء تصدير البيانات إلى Excel:', error);
        alert('حدث خطأ أثناء تصدير البيانات إلى Excel');
    }
}

// دالة لتهيئة DataTables مع دعم اللغة العربية
function initDataTable(tableId, orderColumn = 0, orderDir = 'desc') {
    return $(`#${tableId}`).DataTable({
        "language": {
            "url": "https://cdn.datatables.net/plug-ins/1.13.7/i18n/ar.json"
        },
        "order": [[orderColumn, orderDir]],
        "dom": 'Bfrtip',
        "pageLength": 25,
        "lengthMenu": [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
        "responsive": true,
        "autoWidth": false,
        "scrollX": true,
        "scrollCollapse": true,
        "fixedHeader": true,
        "direction": "rtl",
        "buttons": [
            {
                extend: 'copy',
                text: '<i class="fas fa-copy"></i> نسخ',
                className: 'btn btn-secondary btn-sm',
                exportOptions: {
                    columns: ':not(.no-export)'
                }
            },
            {
                extend: 'print',
                text: '<i class="fas fa-print"></i> طباعة',
                className: 'btn btn-primary btn-sm',
                exportOptions: {
                    columns: ':not(.no-export)'
                },
                customize: function (win) {
                    // تعديل اتجاه الطباعة
                    $(win.document.body).css('direction', 'rtl');
                    $(win.document.body).css('text-align', 'right');
                    $(win.document.body).find('table').css('direction', 'rtl');
                    $(win.document.body).find('table').css('text-align', 'right');
                }
            },
            {
                extend: 'excel',
                text: '<i class="fas fa-file-excel"></i> Excel',
                className: 'btn btn-success btn-sm',
                exportOptions: {
                    columns: ':not(.no-export)'
                },
                customize: function (xlsx) {
                    // تعديل اتجاه Excel
                    var sheet = xlsx.xl.worksheets['sheet1.xml'];
                    $('row c', sheet).attr('s', '50'); // تعيين نمط الخلايا
                    $('worksheet', sheet).attr('rightToLeft', '1'); // تعيين اتجاه الورقة من اليمين إلى اليسار
                }
            },
            {
                text: '<i class="fas fa-file-pdf"></i> PDF',
                className: 'btn btn-danger btn-sm',
                action: function (e, dt, node, config) {
                    // الحصول على URL الحالي
                    let url = window.location.href;
                    // إضافة معلمة export=print إذا لم تكن موجودة
                    if (url.indexOf('?') !== -1) {
                        if (url.indexOf('export=') !== -1) {
                            url = url.replace(/export=[^&]+/, 'export=print');
                        } else {
                            url += '&export=print';
                        }
                    } else {
                        url += '?export=print';
                    }
                    // إضافة معلمة auto_download_pdf=1 لتنزيل PDF تلقائيًا
                    if (url.indexOf('auto_download_pdf=') === -1) {
                        url += '&auto_download_pdf=1';
                    }
                    // فتح صفحة الطباعة في نافذة جديدة
                    openPrintPage(url);
                }
            }
        ]
    });
}

// دالة لفتح صفحة الطباعة
function openPrintPage(url) {
    // فتح نافذة جديدة مع إعدادات مناسبة للطباعة
    const printWindow = window.open(url, '_blank', 'width=800,height=600');

    // إضافة مستمع حدث لتنفيذ التعديلات بعد تحميل الصفحة
    if (printWindow) {
        printWindow.addEventListener('load', function() {
            try {
                // تعديل اتجاه الصفحة
                const htmlElement = printWindow.document.documentElement;
                const bodyElement = printWindow.document.body;

                // تأكيد أن الصفحة بالاتجاه الصحيح
                htmlElement.setAttribute('dir', 'rtl');
                htmlElement.setAttribute('lang', 'ar');
                bodyElement.setAttribute('dir', 'rtl');

                // إضافة أنماط CSS إضافية
                const styleElement = printWindow.document.createElement('style');
                styleElement.textContent = `
                    * {
                        direction: rtl !important;
                        text-align: right !important;
                    }
                    table {
                        direction: rtl !important;
                    }
                    th, td {
                        text-align: right !important;
                    }
                `;
                printWindow.document.head.appendChild(styleElement);

                // إذا كان هناك طلب لتنزيل PDF تلقائيًا
                const urlParams = new URLSearchParams(printWindow.location.search);
                if (urlParams.get('auto_download_pdf') === '1') {
                    // تأخير قليل للتأكد من تطبيق جميع الأنماط
                    setTimeout(function() {
                        printWindow.print();
                    }, 500);
                }
            } catch (e) {
                console.error('حدث خطأ أثناء تعديل صفحة الطباعة:', e);
            }
        });
    }
}
