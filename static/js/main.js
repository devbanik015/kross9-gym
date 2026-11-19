// Kross 9 Gym - Public Site Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. BMI & Calorie Calculator
    // -------------------------------------------------------------------------
    const bmiForm = document.getElementById('bmiCalculatorForm');
    const bmiResultBox = document.getElementById('bmiResultBox');

    if (bmiForm) {
        bmiForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const weight = parseFloat(document.getElementById('calcWeight').value);
            const height = parseFloat(document.getElementById('calcHeight').value);
            const age = parseInt(document.getElementById('calcAge').value);
            const gender = document.getElementById('calcGender').value;
            const activity = parseFloat(document.getElementById('calcActivity').value);
            const goal = document.getElementById('calcGoal').value;

            if (!weight || !height || !age) {
                alert('Please enter valid weight, height, and age.');
                return;
            }

            // BMI Calculation: kg / (m^2)
            const heightInMeters = height / 100;
            const bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);

            let bmiCategory = '';
            let bmiBadgeColor = '';
            if (bmi < 18.5) {
                bmiCategory = 'Underweight';
                bmiBadgeColor = 'bg-blue-500/20 text-blue-400 border-blue-500/40';
            } else if (bmi >= 18.5 && bmi < 24.9) {
                bmiCategory = 'Optimal / Healthy Weight';
                bmiBadgeColor = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
            } else if (bmi >= 25 && bmi < 29.9) {
                bmiCategory = 'Overweight';
                bmiBadgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
            } else {
                bmiCategory = 'Obese (High Risk)';
                bmiBadgeColor = 'bg-red-500/20 text-red-400 border-red-500/40';
            }

            // BMR (Mifflin-St Jeor)
            let bmr = 0;
            if (gender === 'male') {
                bmr = 10 * weight + 6.25 * height - 5 * age + 5;
            } else {
                bmr = 10 * weight + 6.25 * height - 5 * age - 161;
            }

            // TDEE
            const tdee = bmr * activity;

            // Target Calories based on Goal
            let targetCalories = Math.round(tdee);
            let goalDescription = '';
            let proteinTarget = Math.round(weight * 1.8); // 1.8g per kg bodyweight

            if (goal === 'fat_loss') {
                targetCalories = Math.round(tdee - 500);
                goalDescription = 'Caloric Deficit for accelerated fat burning & lean retention';
            } else if (goal === 'muscle_gain') {
                targetCalories = Math.round(tdee + 350);
                goalDescription = 'Caloric Surplus with high protein for maximum hypertrophy';
            } else {
                goalDescription = 'Maintenance calories to preserve current physique & stamina';
            }

            // Update UI elements
            document.getElementById('resBmiValue').innerText = bmi;
            const resBmiCategory = document.getElementById('resBmiCategory');
            resBmiCategory.innerText = bmiCategory;
            resBmiCategory.className = `text-xs px-2.5 py-1 rounded-full font-bold border ${bmiBadgeColor}`;

            document.getElementById('resCalories').innerText = `${targetCalories} kcal/day`;
            document.getElementById('resProtein').innerText = `${proteinTarget}g / day`;
            document.getElementById('resGoalDesc').innerText = goalDescription;

            bmiResultBox.classList.remove('hidden');
            bmiResultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    }

    // -------------------------------------------------------------------------
    // 2. Free Trial Pass Form Submission
    // -------------------------------------------------------------------------
    const trialPassForm = document.getElementById('trialPassForm');
    if (trialPassForm) {
        trialPassForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = trialPassForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="inline-block animate-spin mr-2">&#9696;</span> Generating Pass...`;
            btn.disabled = true;

            const payload = {
                name: document.getElementById('passName').value,
                phone: document.getElementById('passPhone').value,
                email: document.getElementById('passEmail').value,
                workout_date: document.getElementById('passDate').value
            };

            try {
                const response = await fetch('/api/trial-pass', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    showToast(`Free Pass Generated! Code: ${result.pass_code}`, 'success');
                    window.location.href = result.view_url;
                } else {
                    showToast(result.error || 'Failed to generate trial pass.', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Network error while creating pass.', 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // -------------------------------------------------------------------------
    // 3. Contact Form Submission
    // -------------------------------------------------------------------------
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = contactForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = `<span class="inline-block animate-spin mr-2">&#9696;</span> Sending...`;
            btn.disabled = true;

            const payload = {
                name: document.getElementById('contactName').value,
                phone: document.getElementById('contactPhone').value,
                email: document.getElementById('contactEmail').value,
                message: document.getElementById('contactMessage').value
            };

            try {
                const res = await fetch('/api/contact', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message || 'Message sent successfully!', 'success');
                    contactForm.reset();
                } else {
                    showToast(data.error || 'Failed to send message', 'error');
                }
            } catch (err) {
                console.error(err);
                showToast('Error connecting to server.', 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }
});

// Quick WhatsApp message trigger for plans
function inquirePlan(planName, price) {
    const rawPhone = "917478013363";
    const msg = `Hi Kross 9 Gym! I am interested in joining the ${planName} (₹${price}) plan at your Cooch Behar branch. Could you please share more details?`;
    const url = `https://wa.me/${rawPhone}?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');
}
