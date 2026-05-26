const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const path = require('path');

async function testRealImage() {
  const tempPath = path.join(__dirname, 'sample.jpg');
  try {
    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath), {
      filename: 'sample.jpg',
      contentType: 'image/jpeg',
    });

    console.log("Sending real image to AI service...");
    const response = await axios.post("https://ai-forensiclab-2.onrender.com/api/detect-image", form, {
      headers: form.getHeaders(),
      timeout: 120000
    });
    console.log("Response:", response.data);
    
  } catch (error) {
    if (error.response) {
      console.log("ERROR STATUS:", error.response.status);
      console.log("ERROR DATA:", error.response.data);
    } else {
      console.log("ERROR MESSAGE:", error.message);
    }
  }
}

testRealImage();
