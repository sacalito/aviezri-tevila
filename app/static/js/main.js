document.addEventListener('DOMContentLoaded', function() {
    // Update the current time
    function updateTime() {
        const now = new Date();
        document.getElementById('current-time').textContent = 
            `Current Time: ${now.toLocaleString()}`;
    }
    
    // Initial time update
    updateTime();
    
    // Update time every second
    setInterval(updateTime, 1000);
    
    // Check system status
    async function checkStatus() {
        try {
            const response = await fetch('/api/status', {
                method: 'GET',
                headers: {
                    // You'll need to implement a way to get the token
                    'Authorization': 'Bearer ' + 'FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX'
                }
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            document.getElementById('status-message').textContent = 
                `Status: ${data.status} (Last updated: ${data.time})`;
            
        } catch (error) {
            document.getElementById('status-message').textContent = 
                'Error connecting to server';
            console.error('Error:', error);
        }
    }
    
    // Check status initially
    checkStatus();
    
    // Load scheduled hours
    async function loadHours() {
        try {
            const response = await fetch('/hours', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + 'FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX'
                },
                body: JSON.stringify({})
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            const hoursList = document.getElementById('hours-list');
            
            if (data.hours && data.hours.length) {
                let html = '<ul>';
                data.hours.forEach(hour => {
                    html += `<li>${hour.day}: ${hour.start_time} - ${hour.end_time}</li>`;
                });
                html += '</ul>';
                hoursList.innerHTML = html;
            } else {
                hoursList.innerHTML = 'No scheduled hours found';
            }
            
        } catch (error) {
            document.getElementById('hours-list').textContent = 
                'Error loading schedule';
            console.error('Error:', error);
        }
    }
    
    // Load hours initially
    loadHours();
    
    // Set up button listeners
    document.getElementById('open-btn').addEventListener('click', async function() {
        // Implement open functionality
        alert('Open button clicked - API call would go here');
    });
    
    document.getElementById('close-btn').addEventListener('click', async function() {
        // Implement close functionality
        alert('Close button clicked - API call would go here');
    });
});