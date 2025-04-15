export async function checkUserStatus() {
  try {
    const response = await fetch(
      "http://0.0.0.0:8000/registration/user-status"
    );
    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }
    const data = await response.json();
    return data.user_exists;
  } catch (error) {
    console.error("Error checking user status:", error);
    return false; // หากมีข้อผิดพลาด สมมติว่าไม่มีผู้ใช้
  }
}

export async function sendChatMessage(message, personality = "formal") {
  try {
    const response = await fetch("http://0.0.0.0:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        personality: personality,
      }),
    });

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
}

// ฟังก์ชันดึงประวัติการแชท (ถ้าต้องการใช้ในอนาคต)
export async function getChatHistory(limit = 10) {
  try {
    const response = await fetch(
      `http://0.0.0.0:8000/chat/history?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching chat history:", error);
    return [];
  }
}

// ฟังก์ชันดึงข้อมูลผู้ใช้
export async function getUserInfo() {
  try {
    const response = await fetch("http://0.0.0.0:8000/registration/user-info");

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching user info:", error);
    return null;
  }
}
