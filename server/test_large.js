const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const path = require('path');

async function testLargeFile() {
  const tempPath = path.join(__dirname, 'large_dummy.jpg');
  try {
    // Create a 5MB dummy image
    fs.writeFileSync(tempPath, Buffer.alloc(1024 * 1024 * 5)); 
    
    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath), {
      filename: 'large_dummy.jpg',
      contentType: 'image/jpeg',
    });

    console.log("Sending 5MB to AI service...");
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
  } finally {
    if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
  }
}

testLargeFile();
