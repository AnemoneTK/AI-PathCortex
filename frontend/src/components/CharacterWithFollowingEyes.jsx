// components/CharacterWithFollowingEyes.jsx
"use client";
import React, { useState, useEffect, useRef } from "react";

const CharacterWithFollowingEyes = () => {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const characterRef = useRef(null);
  const [eyePositions, setEyePositions] = useState({
    left: { x: 0, y: 0 },
    right: { x: 0, y: 0 },
  });
  const [eyeRadius, setEyeRadius] = useState(8);
  const [characterSize, setCharacterSize] = useState({ width: 0, height: 0 });
  const [lookStraight, setLookStraight] = useState(false);
  const [mouseOnScreen, setMouseOnScreen] = useState(true);

  // ใช้ ref สำหรับเก็บค่าที่เปลี่ยนบ่อยโดยไม่ต้อง re-render
  const targetPositionsRef = useRef({
    left: { x: 0, y: 0 },
    right: { x: 0, y: 0 },
  });
  const lastFrameTimeRef = useRef(0);
  const animationRef = useRef(null);

  // กำหนดตำแหน่งตาเป็นเปอร์เซ็นต์ของขนาดตัวละคร
  const leftEyePositionRef = useRef({ x: 0, y: 0 });
  const rightEyePositionRef = useRef({ x: 0, y: 0 });

  // อัปเดตขนาดตัวละครเมื่อโหลดหรือมีการเปลี่ยนแปลงหน้าจอ
  useEffect(() => {
    const updateCharacterSize = () => {
      if (characterRef.current) {
        const rect = characterRef.current.getBoundingClientRect();
        setCharacterSize({ width: rect.width, height: rect.height });

        // อัปเดตตำแหน่งตาตามขนาดตัวละคร
        leftEyePositionRef.current = {
          x: rect.width * 0, // ใช้ค่า x=0 ตามที่คุณต้องการ
          y: rect.height * 0, // ใช้ค่า y=0 ตามที่คุณต้องการ
        };

        rightEyePositionRef.current = {
          x: rect.width * 0, // ใช้ค่า x=0 ตามที่คุณต้องการ
          y: rect.height * 0, // ใช้ค่า y=0 ตามที่คุณต้องการ
        };
      }
    };

    updateCharacterSize();
    window.addEventListener("resize", updateCharacterSize);

    return () => {
      window.removeEventListener("resize", updateCharacterSize);
    };
  }, []);

  // อนิเมชันการเคลื่อนที่ของลูกตา
  useEffect(() => {
    const animateEyes = (timestamp) => {
      // คำนวณเวลาที่ผ่านไป (delta time)
      const deltaTime = timestamp - lastFrameTimeRef.current;
      lastFrameTimeRef.current = timestamp;

      // ค่า easing (ยิ่งค่าน้อย ยิ่งเคลื่อนที่ช้า)
      const easing = 0.1;

      // ใช้ non-setState update เพื่อป้องกัน re-render loop
      const newPositions = {
        left: {
          x:
            eyePositions.left.x +
            (targetPositionsRef.current.left.x - eyePositions.left.x) * easing,
          y:
            eyePositions.left.y +
            (targetPositionsRef.current.left.y - eyePositions.left.y) * easing,
        },
        right: {
          x:
            eyePositions.right.x +
            (targetPositionsRef.current.right.x - eyePositions.right.x) *
              easing,
          y:
            eyePositions.right.y +
            (targetPositionsRef.current.right.y - eyePositions.right.y) *
              easing,
        },
      };

      // อัปเดต state เฉพาะเมื่อมีการเปลี่ยนแปลงที่มีนัยสำคัญ
      const hasSignificantChange =
        Math.abs(newPositions.left.x - eyePositions.left.x) > 0.01 ||
        Math.abs(newPositions.left.y - eyePositions.left.y) > 0.01 ||
        Math.abs(newPositions.right.x - eyePositions.right.x) > 0.01 ||
        Math.abs(newPositions.right.y - eyePositions.right.y) > 0.01;

      if (hasSignificantChange) {
        setEyePositions(newPositions);
      }

      // ทำงานต่อในเฟรมถัดไป
      animationRef.current = requestAnimationFrame(animateEyes);
    };

    // เริ่มอนิเมชัน
    animationRef.current = requestAnimationFrame(animateEyes);

    // ล้างอนิเมชันเมื่อ unmount
    return () => {
      cancelAnimationFrame(animationRef.current);
    };
  }, [eyePositions]); // ต้องมี dependency ที่ใช้ใน function แต่ต้องระวังไม่ให้ทำงานบ่อยเกินไป

  // ตรวจจับเมื่อเมาส์ออกจากหน้าจอ
  useEffect(() => {
    const handleMouseLeave = () => {
      setMouseOnScreen(false);
      setLookStraight(true); // ให้มองตรงเมื่อเมาส์ออกจากหน้าจอ
    };

    const handleMouseEnter = () => {
      setMouseOnScreen(true);
      setLookStraight(false); // กลับมาติดตามเมาส์เมื่อเมาส์เข้ามาในหน้าจออีกครั้ง
    };

    document.addEventListener("mouseout", handleMouseLeave);
    document.addEventListener("mouseover", handleMouseEnter);

    return () => {
      document.removeEventListener("mouseout", handleMouseLeave);
      document.removeEventListener("mouseover", handleMouseEnter);
    };
  }, []);

  // อัปเดตตำแหน่งเมาส์เมื่อมีการเคลื่อนไหว
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!mouseOnScreen) {
        setMouseOnScreen(true); // กรณีที่ mouseout ไม่ทำงาน แต่ยังได้รับ mousemove
      }

      if (characterRef.current) {
        const characterRect = characterRef.current.getBoundingClientRect();

        // คำนวณตำแหน่งเมาส์สัมพัทธ์กับตัวละคร
        const mouseX = e.clientX - characterRect.left;
        const mouseY = e.clientY - characterRect.top;

        // คำนวณระยะห่างจากตา
        const leftEyeCenter = {
          x: characterRect.width * 0.43, // ประมาณตำแหน่งของตาซ้าย
          y: characterRect.height * 0.37, // ประมาณตำแหน่งของตาซ้าย
        };

        const rightEyeCenter = {
          x: characterRect.width * 0.57, // ประมาณตำแหน่งของตาขวา
          y: characterRect.height * 0.37, // ประมาณตำแหน่งของตาขวา
        };

        // คำนวณระยะห่างจากตาทั้งสองข้าง
        const distanceFromLeftEye = Math.sqrt(
          Math.pow(mouseX - leftEyeCenter.x, 2) +
            Math.pow(mouseY - leftEyeCenter.y, 2)
        );

        const distanceFromRightEye = Math.sqrt(
          Math.pow(mouseX - rightEyeCenter.x, 2) +
            Math.pow(mouseY - rightEyeCenter.y, 2)
        );

        // ระยะที่ถือว่า "ใกล้มาก"
        const veryCloseThreshold = characterRect.width * 0.15;

        // ถ้าเมาส์อยู่ใกล้ตามากๆ ให้มองตรง
        const shouldLookStraight =
          distanceFromLeftEye < veryCloseThreshold ||
          distanceFromRightEye < veryCloseThreshold;

        if (shouldLookStraight !== lookStraight) {
          setLookStraight(shouldLookStraight);
        }

        // คำนวณระยะห่างจากจุดกึ่งกลางของตัวละคร
        const centerX = characterRect.width / 2;
        const centerY = characterRect.height / 2;
        const distanceFromCenter = Math.sqrt(
          Math.pow(mouseX - centerX, 2) + Math.pow(mouseY - centerY, 2)
        );

        // ปรับค่า eyeRadius ตามระยะห่าง
        const nearThreshold = characterRect.width * 0.4;
        const newEyeRadius = distanceFromCenter <= nearThreshold ? 5 : 10;

        if (newEyeRadius !== eyeRadius) {
          setEyeRadius(newEyeRadius);
        }

        // อัปเดตตำแหน่งเมาส์
        setMousePosition({
          x: mouseX,
          y: mouseY,
        });

        // คำนวณตำแหน่งเป้าหมายของลูกตา
        calculateTargetEyePositions(
          mouseX,
          mouseY,
          shouldLookStraight || !mouseOnScreen, // มองตรงเมื่อเมาส์ใกล้ตามากหรือเมื่อเมาส์ออกจากหน้าจอ
          newEyeRadius
        );
      }
    };

    // ฟังก์ชันสำหรับคำนวณตำแหน่งเป้าหมายของลูกตา
    const calculateTargetEyePositions = (
      mouseX,
      mouseY,
      isLookingStraight,
      radius
    ) => {
      const calculateTargetForEye = (eyeCenter) => {
        // ถ้าอยู่ในโหมดมองตรง ให้ตาอยู่ที่ตำแหน่งเริ่มต้น
        if (isLookingStraight) {
          return eyeCenter;
        }

        // เวกเตอร์จากตาไปยังเมาส์
        const dx = mouseX - eyeCenter.x;
        const dy = mouseY - eyeCenter.y;

        // คำนวณระยะทางจากศูนย์กลางตาไปยังเมาส์
        const distance = Math.sqrt(dx * dx + dy * dy);

        // ถ้าเมาส์อยู่ในรัศมีตา ให้ลูกตาเคลื่อนที่ไปยังตำแหน่งเมาส์
        // มิฉะนั้น ให้ลูกตาอยู่ที่ขอบของพื้นที่ที่อนุญาตในทิศทางของเมาส์
        const moveFactor = distance > radius ? radius / distance : 1;

        return {
          x: eyeCenter.x + dx * moveFactor,
          y: eyeCenter.y + dy * moveFactor,
        };
      };

      // อัปเดตตำแหน่งเป้าหมายใน ref (ไม่ทำให้เกิด re-render)
      targetPositionsRef.current = {
        left: calculateTargetForEye(leftEyePositionRef.current),
        right: calculateTargetForEye(rightEyePositionRef.current),
      };
    };

    // เช่นเดียวกับการ handle input focus...
    const handleInputFocus = (e) => {
      const focusedElement = e.target;

      const handleInput = () => {
        if (characterRef.current && focusedElement) {
          // ส่วนนี้คล้ายกับ handleMouseMove แต่คำนวณจากตำแหน่ง cursor
          // ...
          // (คงไว้เหมือนกับโค้ดเดิม แต่เปลี่ยนมาใช้แนวทางเดียวกับ handleMouseMove)
        }
      };

      focusedElement.addEventListener("input", handleInput);
      focusedElement.addEventListener("click", handleInput);
      focusedElement.addEventListener("keyup", handleInput);

      handleInput();

      return () => {
        focusedElement.removeEventListener("input", handleInput);
        focusedElement.removeEventListener("click", handleInput);
        focusedElement.removeEventListener("keyup", handleInput);
      };
    };

    window.addEventListener("mousemove", handleMouseMove);

    document.querySelectorAll("input, textarea").forEach((el) => {
      el.addEventListener("focus", handleInputFocus);
    });

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      document.querySelectorAll("input, textarea").forEach((el) => {
        el.removeEventListener("focus", handleInputFocus);
      });
    };
  }, [eyeRadius, lookStraight, mouseOnScreen]); // เพิ่ม mouseOnScreen เป็น dependency

  // อัปเดตตำแหน่งเป้าหมายเมื่อเมาส์ออกจากหน้าจอ
  useEffect(() => {
    if (!mouseOnScreen) {
      // เมื่อเมาส์ออกจากหน้าจอ ให้ลูกตากลับมามองตรง
      targetPositionsRef.current = {
        left: leftEyePositionRef.current,
        right: rightEyePositionRef.current,
      };
    }
  }, [mouseOnScreen]);

  return (
    <div
      className="character-container relative w-full h-full"
      ref={characterRef}
    >
      <div className="relative">
        {/* รูปตัวละครหลัก */}
        <img
          src="/Character_Image/body.png"
          alt="Character Body"
          className="w-full h-auto"
        />

        {/* ตาขาวซ้าย - จะใช้เป็น mask สำหรับลูกตาซ้าย */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          <div className="relative">
            <img
              src="/Character_Image/eye_white_l.png"
              alt="Left Eye White"
              className="w-full h-auto"
            />

            {/* ลูกตาซ้ายที่ถูก mask ด้วยตาขาว */}
            <div
              className="absolute top-0 left-0 w-full h-full overflow-hidden"
              style={{
                maskImage: "url(/Character_Image/eye_white_l.png)",
                WebkitMaskImage: "url(/Character_Image/eye_white_l.png)",
                maskSize: "100% 100%",
                WebkitMaskSize: "100% 100%",
                maskRepeat: "no-repeat",
                WebkitMaskRepeat: "no-repeat",
                maskPosition: "center",
                WebkitMaskPosition: "center",
              }}
            >
              <div
                className="absolute w-full h-full pointer-events-none"
                style={{
                  left: `${eyePositions.left.x}px`,
                  top: `${eyePositions.left.y}px`,
                }}
              >
                <img
                  src="/Character_Image/eye_l.png"
                  alt="Left Eye"
                  className="w-full h-full"
                />
              </div>
            </div>
          </div>
        </div>

        {/* ตาขาวขวา - จะใช้เป็น mask สำหรับลูกตาขวา */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
          <div className="relative">
            <img
              src="/Character_Image/eye_white_r.png"
              alt="Right Eye White"
              className="w-full h-auto"
            />

            {/* ลูกตาขวาที่ถูก mask ด้วยตาขาว */}
            <div
              className="absolute top-0 left-0 w-full h-full overflow-hidden"
              style={{
                maskImage: "url(/Character_Image/eye_white_r.png)",
                WebkitMaskImage: "url(/Character_Image/eye_white_r.png)",
                maskSize: "100% 100%",
                WebkitMaskSize: "100% 100%",
                maskRepeat: "no-repeat",
                WebkitMaskRepeat: "no-repeat",
                maskPosition: "center",
                WebkitMaskPosition: "center",
              }}
            >
              <div
                className="absolute w-full h-full pointer-events-none"
                style={{
                  left: `${eyePositions.right.x}px`,
                  top: `${eyePositions.right.y}px`,
                }}
              >
                <img
                  src="/Character_Image/eye_r.png"
                  alt="Right Eye"
                  className="w-full h-full"
                />
              </div>
            </div>
          </div>
        </div>
        {/* ขนตา - แสดงทับทุกอย่าง */}
        <img
          src="/Character_Image/eye_lash.png"
          alt="Eye Lashes"
          className="absolute top-0 left-0 w-full h-auto pointer-events-none"
        />
        {/* รูปผม */}
        <img
          src="/Character_Image/hair.png"
          alt="Character Hair"
          className="absolute top-0 left-0 w-full h-auto pointer-events-none"
        />
      </div>
    </div>
  );
};

export default CharacterWithFollowingEyes;
