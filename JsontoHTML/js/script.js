// عناصر DOM
const bankSelect = document.getElementById('bankSelect');
const senderName = document.getElementById('senderName');
const senderAddress = document.getElementById('senderAddress');
const senderEmail = document.getElementById('senderEmail');

// تحديث بيانات المرسل بناءً على البنك المختار
function updateSenderInfo() {
    const selectedBank = bankSelect.value;
    const bank = bankData[selectedBank];
    
    if (bank) {
        senderName.textContent = bank.name;
        senderAddress.textContent = bank.address;
        senderEmail.textContent = bank.email;
        
        // حفظ البنك المختار
        localStorage.setItem('selectedBank', selectedBank);
    }
}

function printDocument() {
    // إخفاء عناصر التحكم والتعليمات قبل الطباعة
    const controls = document.querySelector('.controls');
    const instructions = document.querySelector('.instructions');
    
    // حفظ الحالة الأصلية
    const originalControlsDisplay = controls.style.display;
    const originalInstructionsDisplay = instructions.style.display;
    
    // إخفاء العناصر
    controls.style.display = 'none';
    instructions.style.display = 'none';
    
    // تفعيل الطباعة
    window.print();
    
    // إعادة العناصر بعد الانتهاء من الطباعة (للتأكد من العمل في حالة الإلغاء)
    setTimeout(() => {
        controls.style.display = originalControlsDisplay;
        instructions.style.display = originalInstructionsDisplay;
    }, 100);
}

function saveAsPDF() {
    alert('لحفظ المستند كـ PDF، استخدم خيار "Print to PDF" في نافذة الطباعة.');
    printDocument();
}

function createHTML() {
    // جمع البيانات الحالية
    const selectedBank = bankSelect.value;
    const bank = bankData[selectedBank];
    const editables = document.querySelectorAll('.editable');
    
    // إنشاء محتوى HTML
    const htmlContent = `<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>طلب تمديد الضمان البنكي - ${editables[0].textContent}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f0f2f5;
            padding: 20px;
            color: #333;
            direction: rtl;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
            padding: 30px;
            border-radius: 5px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .recipient {
            text-align: right;
        }
        
        .salutation {
            text-align: left;
        }
        
        .sender-info {
            text-align: right;
            margin-bottom: 25px;
            line-height: 1.8;
        }
        
        .greeting {
            text-align: right;
            margin: 20px 0;
            font-size: 18px;
        }
        
        .subject {
            margin: 25px 0;
            padding: 15px 0;
            border-top: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
            display: flex;
        }
        
        .subject-label {
            font-weight: bold;
            margin-left: 15px;
            min-width: 70px;
        }
        
        .content {
            margin: 25px 0;
            line-height: 1.8;
            text-align: right;
        }
        
        .address-box {
            border-right: 3px solid #c5c5c5;
            padding: 15px 20px;
            margin: 20px 0;
            background-color: #f9f9f9;
            line-height: 1.8;
        }
        
        .signature {
            margin-top: 50px;
            text-align: left;
            float: left;
        }
        
        .clearfix::after {
            content: "";
            clear: both;
            display: table;
        }
        
        .bold {
            font-weight: bold;
        }
        
        @media print {
            body {
                background-color: white;
                padding: 0;
                margin: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 0;
                margin: 0;
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="recipient">
                <div class="bold">السـادة / ${bankSelect.options[bankSelect.selectedIndex].text}</div>
            </div>
            <div class="salutation">
                <div>المحترمين</div>
            </div>
        </div>
        
        <div class="sender-info">
            <div class="bold">${bank.name}</div>
            <div>${bank.address}</div>
            <div>${bank.email}</div>
        </div>
        
        <div class="greeting">
            <div>السَّلام عليكُم ورحمَة الله وبركاتِه</div>
        </div>
        
        <div class="subject">
            <div class="subject-label">الموضوع:</div>
            <div>
                طلب تمديد الضمان البنكي رقم (${editables[0].textContent}) والعائد للعقد رقم (${editables[1].textContent}).
            </div>
        </div>
        
        <div class="content">
            <p>
                إشارة الى الضمان البنكي النهائي الموضح أعلاه، والصادر منكم لصالحنا على حساب شركة رؤية القوى للمصاعد 
                بمبلغ قدرة (${editables[2].textContent}) ريال نأمل منكم تمديد فترة سريان الضمان حتى تاريخ ${editables[3].textContent}، 
                مع بقاء الشروط الأخرى دون تغيير، وإفادتنا بذلك من خلال البريد الالكتروني المخصص للضمانات البنكية لدى مستشفى 
                الملك فيصل التخصصي ومركز الأبحاث بالرياض (bgfinance@kfshrc.edu.sa)، 
                كما نأمل منكم إرسال أصل تمديد الضمان الى:
            </p>
            
            <div class="address-box">
                <div class="bold">مستشفى الملك فيصل التخصصي ومركز الأبحاث - الرياض</div>
                <div>ص.ب 3354 الرياض 11211</div>
                <div>مكتب الخدمات الإدارية</div>
            </div>
            
            <p>
                علمًا بأنه في حال عدم تمكن البنك من تمديد الضمان المذكور قبل إنتهاء مدة سريانه فيجب على البنك دفع 
                قيمة الضمان الينا حسب النظام.
            </p>
            
            <p style="margin-top: 25px;">وَتفضَّلوا بِقبُول خَالِص تحيَّاتي</p>
        </div>
        
        <div class="clearfix">
            <div class="signature">
                <div class="bold">مُدير الإدارة العامَّة للعمليَّات المحاسبيَّة</div>
                <div class="bold">سَامِي بن عبَّاس الفايز</div>
            </div>
        </div>
    </div>
</body>
</html>`;
    
    // إنشاء ملف قابل للتحميل
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `طلب_تمديد_الضمان_${editables[0].textContent}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert('تم إنشاء صفحة HTML بنجاح وتم تحميلها.');
}

function resetDocument() {
    if(confirm('هل أنت متأكد من إعادة تعيين المستند إلى الحالة الأصلية؟ سيتم فقدان جميع التغييرات.')) {
        // إعادة تعيين جميع الحقول القابلة للتعديل إلى قيمها الأصلية
        const editables = document.querySelectorAll('.editable');
        const originalValues = [
            'M113528', 
            '434153', 
            '20.000.00', 
            '30 يوليو 2026م'
        ];
        
        editables.forEach((editable, index) => {
            editable.textContent = originalValues[index];
        });
        
        // إعادة تعيين قائمة البنوك
        bankSelect.value = 'alahli';
        updateSenderInfo();
        
        // مسح التخزين المحلي
        localStorage.clear();
        
        alert('تم إعادة تعيين المستند إلى الحالة الأصلية.');
    }
}

// الحفظ التلقائي للمحتوى في localStorage
document.addEventListener('DOMContentLoaded', function() {
    const editables = document.querySelectorAll('.editable');
    
    // تحميل البنك المحفوظ إذا كان متاحًا
    const savedBank = localStorage.getItem('selectedBank');
    if (savedBank) {
        bankSelect.value = savedBank;
    }
    
    // تحديث معلومات المرسل بناءً على البنك المحدد
    updateSenderInfo();
    
    // حفظ البنك عند التغيير
    bankSelect.addEventListener('change', updateSenderInfo);
    
    // تحميل المحتوى المحفوظ إذا كان متاحًا
    editables.forEach((editable, index) => {
        const savedContent = localStorage.getItem(`editable-${index}`);
        if (savedContent) {
            editable.textContent = savedContent;
        }
        
        // الحفظ عند التعديل
        editable.addEventListener('input', function() {
            localStorage.setItem(`editable-${index}`, this.textContent);
        });
    });
});