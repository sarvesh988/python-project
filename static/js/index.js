
// JavaScript for sending SMS
function sendSMS() {
    const form = document.getElementById('smsForm');
    const formData = new FormData(form);

    const number = formData.get('number');
    const message = formData.get('message');
    const delayMinutes = formData.get('delay_minutes') || 0;

    fetch('/handle_sms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            number: number,
            message: message,
            delay_minutes: delayMinutes
        })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('result').innerText = data.message;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('result').innerText = 'An error occurred.';
        });
}


//  ----------------Photo Capture ----------------
function capturePhoto() {
    const ip = document.getElementById('camera_ip').value;
    if (ip) {
        fetch('/capture_photo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ip: ip }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.message.startsWith("Photo captured")) {
                    // Display the captured photo
                    const img = document.getElementById('photo');
                    img.src = `/image/${data.message.split(' ')[4]}`;
                    img.style.display = 'block';
                    document.getElementById('result').innerText = data.message;
                } else {
                    document.getElementById('result').innerText = data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('result').innerText = 'An error occurred while capturing the photo.';
            });
    } else {
        document.getElementById('result').innerText = 'Please enter a valid IP address.';
    }
}



// ---------------------send email --------------------------------
function sendEmail() {
    const form = document.getElementById('emailForm');
    const formData = new FormData(form);

    const delaySeconds = parseInt(formData.get('delay_seconds'), 10);

    if (isNaN(delaySeconds) || delaySeconds < 0) {
        document.getElementById('result').innerText = 'Invalid delay time.';
        return;
    }

    const actionUrl = delaySeconds > 0 ? '/send_delayed_email' : '/send_email';

    fetch(actionUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            to_email: formData.get('to_email'),
            subject: formData.get('subject'),
            body: formData.get('body'),
            delay_seconds: delaySeconds,
        }),
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('result').innerText = data.message;
        })
        .catch(error => {
            document.getElementById('result').innerText = 'An error occurred: ' + error;
        });
}




//  -----------------Whatsapp Message----------------
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('#WhatMsg form');
    if (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent the default form submission

            const formData = new FormData(form);

            fetch('/send_whatsapp', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('WhatsApp message sent successfully!');
                    } else {
                        console.log('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const sections = [
        'CallSomeone', 'SMS', 'googlequery', 'SearchBing', 'SearchGoogle',
        'CapturePhoto', 'mailcard', 'EC2', 'ec2opencv2', 'insta', 'facecrop', 'imagefilter', 'texttospeak', 'sunglassSet', 'WhatsappMsg', 'swipimage', 'CustomImg'
    ];

    function toggleSections(idsToShow) {
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                if (idsToShow.includes(id)) {
                    element.classList.add('active');
                    element.classList.remove('exiting');
                } else {
                    element.classList.remove('active');
                    element.classList.add('exiting');
                    setTimeout(() => {
                        element.classList.remove('exiting');
                    }, 500); // Match the duration of the CSS transition
                }
            }
        });
    }

    function resetButtonStyles() {
        document.querySelectorAll('#ContainerBtn .btn').forEach(btn => {
            btn.style.backgroundColor = '';
            btn.style.color = '';
        });
    }

    document.getElementById('allBtn').addEventListener('click', function () {
        toggleSections(sections);
        resetButtonStyles();
        this.style.backgroundColor = 'black';
        this.style.color = 'white';
    });

    document.getElementById('PythonBtn').addEventListener('click', function () {
        toggleSections(['CallSomeone', 'SMS', 'mailcard', 'insta', 'imagefilter', 'facecrop', 'texttospeak', 'sunglassSet', 'WhatsappMsg', 'swipimage', 'CustomImg']);
        resetButtonStyles();
        this.style.backgroundColor = 'black';
        this.style.color = 'white';
    });

    document.getElementById('OpenCv2').addEventListener('click', function () {
        toggleSections(['ec2opencv2', 'CapturePhoto']);
        resetButtonStyles();
        this.style.backgroundColor = 'black';
        this.style.color = 'white';
    });

    document.getElementById('AWSService').addEventListener('click', function () {
        toggleSections(['EC2']);
        resetButtonStyles();
        this.style.backgroundColor = 'black';
        this.style.color = 'white';
    });

    document.getElementById('otherTasksBtn').addEventListener('click', function () {
        toggleSections(['googlequery', 'SearchBing', 'SearchGoogle']);
        resetButtonStyles();
        this.style.backgroundColor = 'black';
        this.style.color = 'white';
    });

    // Show all projects by default
    toggleSections(sections); // Display all sections initially
});



// --------------------------------sunglass-----------------------

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const context = canvas.getContext('2d');
let capturedImage = null;
let stream = null;

// Start the camera when the button is clicked
document.getElementById('start-camera-button').addEventListener('click', () => {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(st => {
            stream = st;
            video.srcObject = stream;
            document.getElementById('video-container').style.display = 'block'; // Show video container
        })
        .catch(error => {
            console.error('Error accessing the camera:', error);
        });
});

// Capture the image from the video stream when the button is clicked
document.getElementById('capture-button').addEventListener('click', () => {
    if (!video.srcObject) {
        alert("Please start the camera first.");
        return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    capturedImage = canvas.toDataURL('image/jpeg');
});

// Apply the selected accessory and send the image to the server
document.getElementById('apply-accessory-button').addEventListener('click', () => {
    if (!capturedImage) {
        alert("Please capture an image first.");
        return;
    }

    const accessory = document.getElementById('accessory-select').value;

    fetch('/add_accessory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: capturedImage, accessory })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                const resultImage = new Image();
                resultImage.src = `data:image/jpeg;base64,${data.image}`;
                resultImage.onload = () => {
                    context.drawImage(resultImage, 0, 0, canvas.width, canvas.height);
                }
            }
        })
        .catch(error => console.error('Error:', error));
});

// Save the processed image
document.getElementById('save-button').addEventListener('click', () => {
    if (!capturedImage) {
        alert("Please capture an image first.");
        return;
    }

    const link = document.createElement('a');
    link.download = 'accessory_image.jpg';
    link.href = canvas.toDataURL('image/jpeg');
    link.click();
});


// -------------------image swip-------------------
document.getElementById('upload-form').addEventListener('submit', function (event) {
    event.preventDefault();

    let formData = new FormData();
    formData.append('file1', document.getElementById('file1').files[0]);
    formData.append('file2', document.getElementById('file2').files[0]);

    fetch('/swap_faces', {
        method: 'POST',
        body: formData
    })
        .then(response => response.blob())
        .then(blob => {
            let imgUrl = URL.createObjectURL(blob);
            document.getElementById('output-img').src = imgUrl;
        })
        .catch(error => console.error('Error:', error));
});



document.getElementById('startButton').addEventListener('click', function () {
    fetch('/start_detection', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            document.getElementById('status').textContent = data.message;
        })
        .catch(error => {
            console.error('Error starting detection:', error);
            document.getElementById('status').textContent = 'Error starting detection.';
        });
});

document.getElementById('uploadForm').onsubmit = function (event) {
    event.preventDefault();
    let formData = new FormData(this);
    fetch('/uploadfilter', {
        method: 'POST',
        body: formData
    })
        .then(response => response.blob())
        .then(blob => {
            document.getElementById('result').src = URL.createObjectURL(blob);
        })
        .catch(error => {
            console.error('Error:', error);
        });
};

document.getElementById('captureForm').onsubmit = function (event) {
    event.preventDefault();
    let formData = new FormData(this);
    fetch('/capture', {
        method: 'POST',
        body: formData
    })
        .then(response => response.blob())
        .then(blob => {
            document.getElementById('result').src = URL.createObjectURL(blob);
        })
        .catch(error => {
            console.error('Error:', error);
        });
};


// ---------------------------------google search---------------------
document.getElementById('searchForm').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent form from submitting the traditional way

    const query = document.getElementById('query').value;
    fetch('/google_search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                let resultsText = 'Top 5 Results:\n\n';
                data.results.forEach((result, index) => {
                    resultsText += `${index + 1}. ${result}\n`;
                });
                alert(resultsText);
            } else {
                alert('No results found.');
            }
        })
        .catch(error => console.error('Error:', error));
});

// ---------------------------swip image------------------------
document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('file1', document.getElementById('image1').files[0]);
    formData.append('file2', document.getElementById('image2').files[0]);

    const response = await fetch('/swap_faces', {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        document.getElementById('outputImage').src = url;
    } else {
        const errorData = await response.json();
        alert(errorData.error);
    }
});

// -----------------------------speak-------------------------
document.getElementById('speakForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const text = document.getElementById('text').value;

    fetch('/speak', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'text': text
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Text has been spoken!');
            } else {
                alert('Error in speaking text.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
});

// ---------------------------custom image------------------------
document.getElementById('shape').addEventListener('input', function () {
    const shape = this.value.toLowerCase();
    document.getElementById('line-options').style.display = shape === 'line' ? 'block' : 'none';
    document.getElementById('circle-options').style.display = shape === 'circle' ? 'block' : 'none';
});