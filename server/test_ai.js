const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const path = require('path');

async function testAI() {
  try {
    // Create a dummy image
    const tempPath = path.join(__dirname, 'dummy.jpg');
    fs.writeFileSync(tempPath, Buffer.alloc(1024 * 10)); // 10KB dummy image
    
    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath), {
      filename: 'dummy.jpg',
      contentType: 'image/jpeg',
    });

    console.log("Sending to AI service...");
    const response = await axios.post("https://ai-forensiclab-2.onrender.com/api/detect-image", form, {
      headers: form.getHeaders()
    });
    console.log("Response:", response.data);
    
    fs.unlinkSync(tempPath);
  } catch (error) {
    if (error.response) {
      console.log("ERROR STATUS:", error.response.status);
      console.log("ERROR DATA:", error.response.data);
    } else {
      console.log("ERROR MESSAGE:", error.message);
    }
  }
}

testAI();
