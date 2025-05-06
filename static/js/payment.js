document.addEventListener('DOMContentLoaded', function() {
    // Card number input formatting
    const cardNumberInput = document.querySelector('.card-number-input');
    const cardNumberBox = document.querySelector('.card-number-box');

    if (cardNumberInput && cardNumberBox) {
        cardNumberInput.addEventListener('input', function() {
            // Remove non-numeric characters
            let value = this.value.replace(/\D/g, '');

            // Limit to 16 digits
            if (value.length > 16) {
                value = value.slice(0, 16);
            }

            // Update input value
            this.value = value;

            // Format for display with spaces
            let formattedValue = '';
            for (let i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formattedValue += ' ';
                }
                formattedValue += value[i];
            }

            // Update card number box
            cardNumberBox.textContent = formattedValue || '################';
        });
    }

    // Card holder name input
    const cardHolderInput = document.querySelector('.card-holder-input');
    const cardHolderName = document.querySelector('.card-holder-name');

    if (cardHolderInput && cardHolderName) {
        cardHolderInput.addEventListener('input', function() {
            cardHolderName.textContent = this.value || 'full name';
        });
    }

    // Expiry month input
    const monthInput = document.querySelector('.month-input');
    const expMonth = document.querySelector('.exp-month');

    if (monthInput && expMonth) {
        monthInput.addEventListener('change', function() {
            expMonth.textContent = this.value || 'mm';
        });
    }

    // Expiry year input
    const yearInput = document.querySelector('.year-input');
    const expYear = document.querySelector('.exp-year');

    if (yearInput && expYear) {
        yearInput.addEventListener('change', function() {
            expYear.textContent = this.value || 'yy';
        });
    }

    // CVV input
    const cvvInput = document.querySelector('.cvv-input');
    const cvvBox = document.querySelector('.cvv-box');

    if (cvvInput && cvvBox) {
        cvvInput.addEventListener('input', function() {
            // Remove non-numeric characters
            let value = this.value.replace(/\D/g, '');

            // Limit to 4 digits
            if (value.length > 4) {
                value = value.slice(0, 4);
            }

            // Update input value
            this.value = value;

            // Update CVV box
            cvvBox.textContent = value;
        });
    }

    // Card flip on CVV focus
    const front = document.querySelector('.front');
    const back = document.querySelector('.back');

    if (cvvInput && front && back) {
        cvvInput.addEventListener('mouseenter', function() {
            front.style.transform = 'perspective(1000px) rotateY(-180deg)';
            back.style.transform = 'perspective(1000px) rotateY(0deg)';
        });

        cvvInput.addEventListener('mouseleave', function() {
            front.style.transform = 'perspective(1000px) rotateY(0deg)';
            back.style.transform = 'perspective(1000px) rotateY(180deg)';
        });

        cvvInput.addEventListener('focus', function() {
            front.style.transform = 'perspective(1000px) rotateY(-180deg)';
            back.style.transform = 'perspective(1000px) rotateY(0deg)';
        });

        cvvInput.addEventListener('blur', function() {
            front.style.transform = 'perspective(1000px) rotateY(0deg)';
            back.style.transform = 'perspective(1000px) rotateY(180deg)';
        });
    }

    // Form validation
    const paymentForm = document.getElementById('payment-form');

    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            let isValid = true;

            // Validate card number
            if (cardNumberInput && cardNumberInput.value.length < 16) {
                isValid = false;
                cardNumberInput.classList.add('error');
            } else if (cardNumberInput) {
                cardNumberInput.classList.remove('error');
            }

            // Validate card holder
            if (cardHolderInput && !cardHolderInput.value.trim()) {
                isValid = false;
                cardHolderInput.classList.add('error');
            } else if (cardHolderInput) {
                cardHolderInput.classList.remove('error');
            }

            // Validate expiry month
            if (monthInput && monthInput.value === 'month') {
                isValid = false;
                monthInput.classList.add('error');
            } else if (monthInput) {
                monthInput.classList.remove('error');
            }

            // Validate expiry year
            if (yearInput && yearInput.value === 'year') {
                isValid = false;
                yearInput.classList.add('error');
            } else if (yearInput) {
                yearInput.classList.remove('error');
            }

            // Validate CVV
            if (cvvInput && cvvInput.value.length < 3) {
                isValid = false;
                cvvInput.classList.add('error');
            } else if (cvvInput) {
                cvvInput.classList.remove('error');
            }

            if (!isValid) {
                e.preventDefault();

                // Show error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'error-message payment-error';
                errorMsg.textContent = 'يرجى التأكد من إدخال جميع البيانات بشكل صحيح';

                // Remove any existing error message
                const existingError = document.querySelector('.payment-error');
                if (existingError) {
                    existingError.remove();
                }

                // Add error message to form
                paymentForm.prepend(errorMsg);

                // Scroll to top of form
                paymentForm.scrollIntoView({ behavior: 'smooth' });
            } else {
                // Show loading state
                const submitBtn = paymentForm.querySelector('.submit-btn');
                submitBtn.disabled = true;
                submitBtn.value = 'جاري المعالجة...';
                submitBtn.classList.add('loading');

                // For testing purposes, we can simulate a successful payment
                // In production, the form would be submitted to the server
                if (submitBtn.classList.contains('test-mode')) {
                    e.preventDefault();

                    setTimeout(() => {
                        // Show success message
                        paymentForm.innerHTML = `
                            <div class="payment-success">
                                <i class="fas fa-check-circle"></i>
                                <h2>تمت عملية الدفع بنجاح!</h2>
                                <p>تم تفعيل اشتراكك بنجاح. يمكنك الآن الاستمتاع بجميع مميزات الباقة.</p>
                                <a href="/profile/" class="btn btn-primary">العودة إلى الملف الشخصي</a>
                            </div>
                        `;
                    }, 2000);
                }
            }
        });
    }

    // Get subscription package from URL parameters
    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        const results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    }

    // Set package and price from URL parameters
    const packageParam = getUrlParameter('package');
    const priceParam = getUrlParameter('price');

    if (packageParam && priceParam && paymentForm) {
        const packageInput = document.querySelector('input[name="package"]');
        const priceInput = document.querySelector('input[name="price"]');

        if (packageInput) packageInput.value = packageParam;
        if (priceInput) priceInput.value = priceParam;

        // Add order summary if it exists
        const orderSummary = document.querySelector('.order-summary');
        if (orderSummary) {
            const packageName = packageParam === 'basic' ? 'الباقة الأساسية' : 'الباقة الاحترافية';
            const price = parseFloat(priceParam);
            const tax = price * 0.15; // 15% VAT
            const total = price + tax;

            const itemName = orderSummary.querySelector('.item-name');
            const itemPrice = orderSummary.querySelector('.item-price');
            const taxValue = orderSummary.querySelector('.summary-item:nth-child(2) .item-price');
            const totalValue = orderSummary.querySelector('.total-price');

            if (itemName) itemName.textContent = packageName;
            if (itemPrice) itemPrice.textContent = price.toFixed(2) + ' ريال';
            if (taxValue) taxValue.textContent = tax.toFixed(2) + ' ريال';
            if (totalValue) totalValue.textContent = total.toFixed(2) + ' ريال';
        }
    }
});