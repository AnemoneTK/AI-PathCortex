import React, { useState } from "react";
import {
  User,
  GraduationCap,
  Code,
  Briefcase,
  FileText,
  CheckCircle,
  X,
  Upload,
  Plus,
  Trash2,
} from "lucide-react";

// Registration flow component
const UserRegistration = () => {
  // Track current step in the registration flow
  const [currentStep, setCurrentStep] = useState(0);

  // State for user data
  const [userData, setUserData] = useState({
    name: "",
    education: {
      status: "student", // 'student', 'graduate', 'working'
      year: 1,
      institution: "",
    },
    skills: [],
    programmingLanguages: [], // เปลี่ยนจาก array ของ string เป็น array ของ object
    tools: [], // เปลี่ยนจาก array ของ string เป็น array ของ object
    projects: [],
    resume: null,
  });

  // Input field for adding new tags (skills, languages, tools)
  const [tagInput, setTagInput] = useState({ name: '', proficiency: 4 });
  const [showProficiencySlider, setShowProficiencySlider] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState([]);
  const [selectedTagType, setSelectedTagType] = useState('skills');

  // Predefined options for different tag types
  const predefinedOptions = {
    skills: [
      "UI Design",
      "UX Design",
      "Web Design",
      "Graphic Design",
      "Project Management",
      "Agile",
      "Scrum",
      "Testing",
      "Quality Assurance",
      "DevOps",
      "Database Design",
      "SEO",
      "Digital Marketing",
      "Content Writing",
      "Data Analysis",
      "Game Development",
      "Mobile App Development",
      "API Design",
      "Cloud Computing",
      "Machine Learning",
      "Artificial Intelligence",
      "Cybersecurity",
      "Blockchain",
      "IoT",
    ],
    programmingLanguages: [
      "JavaScript",
      "TypeScript",
      "Python",
      "Java",
      "C#",
      "C++",
      "C",
      "PHP",
      "Ruby",
      "Swift",
      "Kotlin",
      "Go",
      "Rust",
      "Scala",
      "R",
      "Dart",
      "HTML",
      "CSS",
      "SQL",
      "Bash",
      "PowerShell",
      "MATLAB",
      "Objective-C",
      "Perl",
      "Haskell",
      "Lua",
    ],
    tools: [
      "VS Code",
      "Visual Studio",
      "IntelliJ IDEA",
      "PyCharm",
      "WebStorm",
      "Figma",
      "Adobe XD",
      "Sketch",
      "Photoshop",
      "Illustrator",
      "Git",
      "GitHub",
      "GitLab",
      "Bitbucket",
      "Docker",
      "Kubernetes",
      "AWS",
      "Azure",
      "Google Cloud",
      "Firebase",
      "Jira",
      "Trello",
      "Asana",
      "Notion",
      "Jenkins",
      "Travis CI",
      "CircleCI",
      "Postman",
      "Jupyter Notebook",
      "Slack",
      "Discord",
      "Zoom",
      "Miro",
      "Tableau",
      "Power BI",
      "Unity",
      "Unreal Engine",
      "Android Studio",
      "Xcode",
    ],
  };

  // State for current project being edited
  const [currentProject, setCurrentProject] = useState({
    name: "",
    description: "",
    role: "",
    responsibilities: "",
    technologies: [],
  });

  // State for project technology input
  const [techInput, setTechInput] = useState("");

  // Handle form field changes
  const handleChange = (e) => {
    const { name, value } = e.target;

    // Handle nested properties
    if (name.includes(".")) {
      const [parent, child] = name.split(".");
      setUserData({
        ...userData,
        [parent]: {
          ...userData[parent],
          [child]: value,
        },
      });
    } else {
      setUserData({
        ...userData,
        [name]: value,
      });
    }
  };

  // Handle tag input changes
  const handleTagInputChange = (e) => {
    const input = e.target.value;
    setTagInput({
      ...tagInput,
      name: input
    });
  
    // Filter options based on input
    if (input.trim() !== "") {
      const options = predefinedOptions[selectedTagType];
      const filtered = options.filter(
        (option) =>
          option.toLowerCase().includes(input.toLowerCase()) &&
          !userData[selectedTagType].some(skill => 
            typeof skill === 'object' ? skill.name === option : skill === option
          )
      );
      setFilteredOptions(filtered);
    } else {
      setFilteredOptions([]);
    }
  };

  // Add a new tag (skill, language, or tool)
const addTag = () => {
  if (tagInput.name.trim() === "") return;

  if (selectedTagType === "skills") {
    if (!userData.skills.some(skill => typeof skill === 'object' ? skill.name === tagInput.name : skill === tagInput.name)) {
      setUserData({
        ...userData,
        skills: [...userData.skills, { name: tagInput.name, proficiency: tagInput.proficiency }]
      });
    }
  } else if (selectedTagType === "programmingLanguages") {
    if (!userData.programmingLanguages.some(lang => typeof lang === 'object' ? lang.name === tagInput.name : lang === tagInput.name)) {
      setUserData({
        ...userData,
        programmingLanguages: [...userData.programmingLanguages, { name: tagInput.name, proficiency: tagInput.proficiency }]
      });
    }
  } else if (selectedTagType === "tools") {
    if (!userData.tools.some(tool => typeof tool === 'object' ? tool.name === tagInput.name : tool === tagInput.name)) {
      setUserData({
        ...userData,
        tools: [...userData.tools, { name: tagInput.name, proficiency: tagInput.proficiency }]
      });
    }
  }

  setTagInput({ name: '', proficiency: 4 });
  setFilteredOptions([]);
  setShowProficiencySlider(false);
};

  // Add a tag from suggestions
const addSuggestedTag = (tag) => {
  if (selectedTagType === "skills") {
    if (!userData.skills.some(skill => typeof skill === 'object' ? skill.name === tag : skill === tag)) {
      setTagInput({ name: tag, proficiency: 4 });
      setShowProficiencySlider(true);
    }
  } else if (selectedTagType === "programmingLanguages") {
    if (!userData.programmingLanguages.some(lang => typeof lang === 'object' ? lang.name === tag : lang === tag)) {
      setTagInput({ name: tag, proficiency: 4 });
      setShowProficiencySlider(true);
    }
  } else if (selectedTagType === "tools") {
    if (!userData.tools.some(tool => typeof tool === 'object' ? tool.name === tag : tool === tag)) {
      setTagInput({ name: tag, proficiency: 4 });
      setShowProficiencySlider(true);
    }
  }
};


  // Remove a tag
const removeTag = (type, tag) => {
  if (type === "skills") {
    setUserData({
      ...userData,
      skills: userData.skills.filter(skill => 
        typeof skill === 'object' && typeof tag === 'object' 
          ? skill.name !== tag.name 
          : typeof skill === 'string' && typeof tag === 'string'
            ? skill !== tag
            : true
      )
    });
  } else if (type === "programmingLanguages") {
    setUserData({
      ...userData,
      programmingLanguages: userData.programmingLanguages.filter(lang => 
        typeof lang === 'object' && typeof tag === 'object' 
          ? lang.name !== tag.name 
          : typeof lang === 'string' && typeof tag === 'string'
            ? lang !== tag
            : true
      )
    });
  } else if (type === "tools") {
    setUserData({
      ...userData,
      tools: userData.tools.filter(tool => 
        typeof tool === 'object' && typeof tag === 'object' 
          ? tool.name !== tag.name 
          : typeof tool === 'string' && typeof tag === 'string'
            ? tool !== tag
            : true
      )
    });
  }
};

  // Add technology to current project
  const addProjectTech = () => {
    if (techInput.trim() === "") return;

    if (!currentProject.technologies.includes(techInput.trim())) {
      setCurrentProject({
        ...currentProject,
        technologies: [...currentProject.technologies, techInput.trim()],
      });
      setTechInput("");
    }
  };

  const handleProjectChange = (e) => {
    const { name, value } = e.target;
    setCurrentProject({
      ...currentProject,
      [name]: value,
    });
  };

  const handleProficiencyChange = (value) => {
    setTagInput({...tagInput, proficiency: parseInt(value)});
  };

  // Remove technology from current project
  const removeProjectTech = (tech) => {
    setCurrentProject({
      ...currentProject,
      technologies: currentProject.technologies.filter((item) => item !== tech),
    });
  };

  // Add current project to user data
  const addProject = () => {
    // Validate project has at least a name
    if (currentProject.name.trim() === "") return;

    setUserData({
      ...userData,
      projects: [...userData.projects, { ...currentProject, id: Date.now() }],
    });

    // Reset current project
    setCurrentProject({
      name: "",
      description: "",
      role: "",
      responsibilities: "",
      technologies: [],
    });
  };

  // Remove project from user data
  const removeProject = (projectId) => {
    setUserData({
      ...userData,
      projects: userData.projects.filter((project) => project.id !== projectId),
    });
  };

  // Handle resume file upload
  const handleResumeUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      setUserData({
        ...userData,
        resume: e.target.files[0],
      });
    }
  };

  // Submit the registration form
  const handleSubmit = async () => {
    try {
      // แปลงข้อมูลให้อยู่ในรูปแบบที่ API ต้องการ
      const apiUserData = {
        name: userData.name,
        institution: userData.education.institution,
        education_status: userData.education.status,
        year: userData.education.year,
        skills: userData.skills.map((skill) => ({
          name: typeof skill === 'object' ? skill.name : skill,
          proficiency: typeof skill === 'object' ? skill.proficiency : 4,
        })),
        programming_languages: userData.programmingLanguages.map((lang) => ({
          name: typeof lang === 'object' ? lang.name : lang,
          proficiency: typeof lang === 'object' ? lang.proficiency : 4,
        })),
        tools: userData.tools.map((tool) => ({
          name: typeof tool === 'object' ? tool.name : tool,
          proficiency: typeof tool === 'object' ? tool.proficiency : 4,
        })),
        projects: userData.projects.map((project) => ({
          name: project.name,
          description: project.description,
          technologies: project.technologies,
          role: project.role,
        })),
        work_experiences: [], 
      };
  
      // Create FormData for file upload
      const formData = new FormData();
      
      // เพิ่มข้อมูลผู้ใช้
      formData.append("user_data", JSON.stringify(apiUserData));
  
      // Add resume file if exists
      if (userData.resume) {
        formData.append("resume", userData.resume);
      }
  
      // Send to backend API
      const response = await fetch("http://0.0.0.0:8000/registration/", {
        method: "POST",
        body: formData,
      });
  
      if (response.ok) {
        // Move to success step
        setCurrentStep(6);
        
        // เปลี่ยนหน้าทันทีหลังลงทะเบียนสำเร็จ
        window.location.href = "/chat";
      } else {
        // Try to parse error response
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (parseError) {
          // If response is not JSON, get text or status
          try {
            errorData.detail = await response.text();
          } catch (textError) {
            errorData.detail = `HTTP Error ${response.status}: ${response.statusText}`;
          }
        }
        
        console.error("Registration error:", response.status, errorData);
        alert(
          `Registration failed: ${errorData.detail || "Please try again."}`
        );
      }
    } catch (error) {
      console.error("Error during registration:", error);
      alert("Registration failed. Please try again.");
    }
  };

  // Navigation between steps
  const nextStep = () => {
    setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  // Render different steps based on currentStep
  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="flex flex-col items-center text-center">
            <div className="mb-8 p-4 bg-blue-100 rounded-full">
              <User className="h-16 w-16 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold mb-4">
              ยินดีต้อนรับสู่ AI Buddy
            </h2>
            <p className="mb-6 text-gray-600 max-w-md">
              ที่ปรึกษาด้านวิทยาการคอมพิวเตอร์ที่จะช่วยให้คำแนะนำที่เหมาะสมกับความต้องการของคุณ
            </p>
            <p className="mb-8 text-gray-600">
              กรุณากรอกข้อมูลเพื่อเริ่มต้นการใช้งาน
            </p>
            <button
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={nextStep}
            >
              เริ่มกรอกข้อมูล
            </button>
          </div>
        );

      case 1:
        return (
          <div className="w-full max-w-md">
            <div className="flex items-center mb-6">
              <div className="p-2 bg-blue-100 rounded-full mr-4">
                <User className="h-6 w-6 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold">ข้อมูลส่วนตัว</h2>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ชื่อที่ต้องการให้เรียก
              </label>
              <input
                type="text"
                name="name"
                value={userData.name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="ชื่อของคุณ"
                required
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                สถาบันการศึกษา
              </label>
              <input
                type="text"
                name="education.institution"
                value={userData.education.institution}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="ชื่อสถาบันการศึกษา"
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                สถานะการศึกษา
              </label>
              <select
                name="education.status"
                value={userData.education.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="student">กำลังศึกษา</option>
                <option value="graduate">จบการศึกษา</option>
                <option value="working">ทำงานแล้ว</option>
              </select>
            </div>

            {userData.education.status === "student" && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ชั้นปี
                </label>
                <select
                  name="education.year"
                  value={userData.education.year}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>ปี 1</option>
                  <option value={2}>ปี 2</option>
                  <option value={3}>ปี 3</option>
                  <option value={4}>ปี 4</option>
                  <option value={5}>ปี 5 หรือมากกว่า</option>
                </select>
              </div>
            )}

            <div className="flex justify-between mt-8">
              <button
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                onClick={prevStep}
              >
                ย้อนกลับ
              </button>
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                onClick={nextStep}
                disabled={!userData.name}
              >
                ถัดไป
              </button>
            </div>
          </div>
        );

        case 2:
  return (
    <div className="w-full max-w-md">
      <div className="flex items-center mb-6">
        <div className="p-2 bg-blue-100 rounded-full mr-4">
          <Code className="h-6 w-6 text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold">ทักษะและความสามารถ</h2>
      </div>

      <div className="mb-6">
        <div className="flex space-x-2 mb-2">
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              selectedTagType === "skills"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
            onClick={() => setSelectedTagType("skills")}
          >
            ทักษะ
          </button>
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              selectedTagType === "programmingLanguages"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
            onClick={() => setSelectedTagType("programmingLanguages")}
          >
            ภาษาโปรแกรม
          </button>
          <button
            className={`px-3 py-1 rounded-full text-sm ${
              selectedTagType === "tools"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
            onClick={() => setSelectedTagType("tools")}
          >
            เครื่องมือ
          </button>
        </div>

        <div className="relative mb-2">
          <div className="flex">
            <input
              type="text"
              value={tagInput.name}
              onChange={handleTagInputChange}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={
                selectedTagType === "skills"
                  ? "พิมพ์เพื่อค้นหาหรือเพิ่มทักษะ"
                  : selectedTagType === "programmingLanguages"
                  ? "พิมพ์เพื่อค้นหาหรือเพิ่มภาษาโปรแกรม"
                  : "พิมพ์เพื่อค้นหาหรือเพิ่มเครื่องมือ"
              }
              onKeyPress={(e) => e.key === "Enter" && (showProficiencySlider ? addTag() : setShowProficiencySlider(true))}
            />
            <button
              className="px-3 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors"
              onClick={() => showProficiencySlider ? addTag() : setShowProficiencySlider(true)}
            >
              {showProficiencySlider ? "เพิ่ม" : "ต่อไป"}
            </button>
          </div>

          {/* Suggestions dropdown */}
          {filteredOptions.length > 0 && !showProficiencySlider && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
              {filteredOptions.map((option, index) => (
                <div
                  key={index}
                  className="px-3 py-2 hover:bg-blue-50 cursor-pointer"
                  onClick={() => addSuggestedTag(option)}
                >
                  {option}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* แก้ไข: เปลี่ยนจาก Proficiency slider เป็น Radio buttons */}
        {showProficiencySlider && (
          <div className="mt-2 mb-4 bg-gray-50 p-3 rounded-lg">
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              ระดับความชำนาญของ "{tagInput.name}" (1-5)
            </label>
            <div className="flex flex-col mt-2">
              <div className="flex justify-between mb-1">
                <span className="text-xs text-gray-500">น้อย</span>
                <span className="text-xs text-gray-500">มาก</span>
              </div>
              
              <div className="flex justify-between">
                {[1, 2, 3, 4, 5].map(num => (
                  <div key={num} className="flex items-center">
                    <input
                      type="radio"
                      id={`proficiency-${num}`}
                      name="proficiency"
                      value={num}
                      checked={tagInput.proficiency === num}
                      onChange={(e) => handleProficiencyChange(e.target.value)}
                      className="mr-1"
                    />
                    <label htmlFor={`proficiency-${num}`} className="text-sm">{num}</label>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-end mt-3 space-x-2">
              <button
                onClick={() => setShowProficiencySlider(false)}
                className="px-3 py-1 text-sm text-gray-600 border border-gray-300 rounded hover:bg-gray-100"
              >
                ยกเลิก
              </button>
              <button
                onClick={addTag}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                เพิ่ม
              </button>
            </div>
          </div>
        )}

        {/* Popular suggestions */}
        {!showProficiencySlider && (
          <div className="mb-3">
            <p className="text-sm text-gray-500 mb-2">ตัวเลือกยอดนิยม:</p>
            <div className="flex flex-wrap gap-2">
              {predefinedOptions[selectedTagType]
                .slice(0, 6)
                .map((option, index) => {
                  // ตรวจสอบว่ามีในรายการแล้วหรือไม่
                  const alreadyAdded = userData[selectedTagType].some(item => 
                    typeof item === 'object' ? item.name === option : item === option
                  );
                  
                  if (alreadyAdded) return null;
                  
                  return (
                    <button
                      key={index}
                      className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm hover:bg-gray-200"
                      onClick={() => addSuggestedTag(option)}
                    >
                      {option}
                    </button>
                  );
                })}
            </div>
          </div>
        )}

        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            {selectedTagType === "skills"
              ? "ทักษะของคุณ"
              : selectedTagType === "programmingLanguages"
              ? "ภาษาโปรแกรมที่คุณเขียนได้"
              : "เครื่องมือที่คุณใช้งานได้"}
          </p>
          <div className="flex flex-wrap gap-2">
            {userData[selectedTagType].map((tag, index) => (
              <div
                key={index}
                className={`px-3 py-1 rounded-full flex items-center ${
                  selectedTagType === "skills" 
                    ? "bg-blue-100 text-blue-800" 
                    : selectedTagType === "programmingLanguages"
                      ? "bg-green-100 text-green-800"
                      : "bg-purple-100 text-purple-800"
                }`}
              >
                <span>
                  {typeof tag === 'object' 
                    ? `${tag.name} (${tag.proficiency})` 
                    : tag}
                </span>
                <button
                  className="ml-2 text-gray-500 hover:text-gray-700"
                  onClick={() => removeTag(selectedTagType, tag)}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
            {userData[selectedTagType].length === 0 && (
              <p className="text-sm text-gray-500 italic">
                ยังไม่มีรายการ
              </p>
            )}
          </div>
        </div>

        <div className="flex justify-between mt-8">
          <button
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            onClick={prevStep}
          >
            ย้อนกลับ
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            onClick={nextStep}
          >
            ถัดไป
          </button>
        </div>
      </div>
    </div>
  );

case 3:
  return (
    <div className="w-full max-w-md">
      <div className="flex items-center mb-6">
        <div className="p-2 bg-blue-100 rounded-full mr-4">
          <Briefcase className="h-6 w-6 text-blue-600" />
        </div>
        <h2 className="text-xl font-semibold">โปรเจกต์ผลงาน</h2>
      </div>

      <div className="bg-gray-50 p-4 rounded-lg mb-6">
        <h3 className="font-medium text-gray-800 mb-3">
          เพิ่มโปรเจกต์ใหม่
        </h3>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ชื่อโปรเจกต์
          </label>
          <input
            type="text"
            name="name"
            value={currentProject.name}
            onChange={handleProjectChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="ชื่อโปรเจกต์"
          />
        </div>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            รายละเอียดโปรเจกต์
          </label>
          <textarea
            name="description"
            value={currentProject.description}
            onChange={handleProjectChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="อธิบายเกี่ยวกับโปรเจกต์"
            rows="2"
          ></textarea>
        </div>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            บทบาท/ตำแหน่งของคุณ
          </label>
          <input
            type="text"
            name="role"
            value={currentProject.role}
            onChange={handleProjectChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="เช่น Front-end Developer"
          />
        </div>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            สิ่งที่คุณรับผิดชอบ
          </label>
          <textarea
            name="responsibilities"
            value={currentProject.responsibilities}
            onChange={handleProjectChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="สิ่งที่คุณรับผิดชอบในโปรเจกต์นี้"
            rows="2"
          ></textarea>
        </div>

        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            เทคโนโลยีที่ใช้
          </label>
          <div className="flex mb-2">
            <input
              type="text"
              value={techInput}
              onChange={(e) => setTechInput(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="เช่น React, Node.js"
              onKeyPress={(e) => e.key === "Enter" && addProjectTech()}
            />
            <button
              className="px-3 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 transition-colors"
              onClick={addProjectTech}
            >
              เพิ่ม
            </button>
          </div>
          
          {/* เพิ่มตัวเลือกยอดนิยมสำหรับเทคโนโลยี */}
          <div className="mb-3">
            <p className="text-sm text-gray-500 mb-2">เทคโนโลยียอดนิยม:</p>
            <div className="flex flex-wrap gap-2">
              {["React", "Angular", "Vue", "Node.js", "Express", "Django", "Flask"].map((option, index) => {
                // ตรวจสอบว่ามีในรายการแล้วหรือไม่
                const alreadyAdded = currentProject.technologies.includes(option);
                
                if (alreadyAdded) return null;
                
                return (
                  <button
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm hover:bg-gray-200"
                    onClick={() => {
                      setCurrentProject({
                        ...currentProject,
                        technologies: [...currentProject.technologies, option]
                      });
                    }}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex flex-wrap gap-2 mt-2">
            {currentProject.technologies.map((tech, index) => (
              <div
                key={index}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full flex items-center"
              >
                <span>{tech}</span>
                <button
                  className="ml-2 text-blue-500 hover:text-blue-700"
                  onClick={() => removeProjectTech(tech)}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <button
          className="w-full px-4 py-2 mt-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
          onClick={addProject}
          disabled={!currentProject.name}
        >
          <Plus size={16} className="mr-2" />
          เพิ่มโปรเจกต์
        </button>
      </div>

      {userData.projects.length > 0 && (
        <div className="mb-6">
          <h3 className="font-medium text-gray-800 mb-3">
            โปรเจกต์ที่เพิ่มแล้ว
          </h3>
          <div className="space-y-3">
            {userData.projects.map((project) => (
              <div
                key={project.id}
                className="border border-gray-200 rounded-lg p-3"
              >
                <div className="flex justify-between">
                  <h4 className="font-medium">{project.name}</h4>
                  <button
                    className="text-red-500 hover:text-red-700"
                    onClick={() => removeProject(project.id)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                {project.role && (
                  <p className="text-sm text-blue-600 mt-1">
                    {project.role}
                  </p>
                )}
                {project.description && (
                  <p className="text-sm text-gray-600 mt-1">
                    {project.description}
                  </p>
                )}
                {project.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {project.technologies.map((tech, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-between mt-8">
        <button
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          onClick={prevStep}
        >
          ย้อนกลับ
        </button>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          onClick={nextStep}
        >
          ถัดไป
        </button>
      </div>
    </div>
  );

      case 4:
        return (
          <div className="w-full max-w-md">
            <div className="flex items-center mb-6">
              <div className="p-2 bg-blue-100 rounded-full mr-4">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <h2 className="text-xl font-semibold">
                อัปโหลด Resume (ไม่บังคับ)
              </h2>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
              {userData.resume ? (
                <div className="flex flex-col items-center">
                  <div className="p-3 bg-green-100 rounded-full mb-3">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                  <p className="font-medium text-gray-800">
                    {userData.resume.name}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {(userData.resume.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <button
                    className="mt-4 px-3 py-1 bg-red-100 text-red-600 rounded-full text-sm hover:bg-red-200 transition-colors"
                    onClick={() => setUserData({ ...userData, resume: null })}
                  >
                    ลบไฟล์
                  </button>
                </div>
              ) : (
                <div>
                  <label className="cursor-pointer flex flex-col items-center">
                    <Upload className="h-12 w-12 text-gray-400 mb-2" />
                    <span className="font-medium text-gray-800">
                      คลิกเพื่ออัปโหลด Resume
                    </span>
                    <span className="text-sm text-gray-500 mt-1">
                      สนับสนุนไฟล์ PDF, DOCX
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.docx,.doc"
                      onChange={handleResumeUpload}
                    />
                  </label>
                </div>
              )}
            </div>

            <div className="flex justify-between mt-8">
              <button
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                onClick={prevStep}
              >
                ย้อนกลับ
              </button>
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                onClick={nextStep}
              >
                ถัดไป
              </button>
            </div>
          </div>
        );

        case 5:
          return (
            <div className="w-full max-w-md">
              <div className="flex items-center mb-6">
                <div className="p-2 bg-blue-100 rounded-full mr-4">
                  <CheckCircle className="h-6 w-6 text-blue-600" />
                </div>
                <h2 className="text-xl font-semibold">ตรวจสอบข้อมูล</h2>
              </div>
        
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-800 border-b pb-2 mb-3">
                  ข้อมูลส่วนตัว
                </h3>
                <p>
                  <span className="font-medium">ชื่อ:</span> {userData.name}
                </p>
                <p>
                  <span className="font-medium">สถาบัน:</span>{" "}
                  {userData.education.institution || "-"}
                </p>
                <p>
                  <span className="font-medium">สถานะการศึกษา:</span>{" "}
                  {userData.education.status === "student"
                    ? `กำลังศึกษาชั้นปีที่ ${userData.education.year}`
                    : userData.education.status === "graduate"
                    ? "จบการศึกษา"
                    : "ทำงานแล้ว"}
                </p>
              </div>
        
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-800 border-b pb-2 mb-3">
                  ทักษะและความสามารถ
                </h3>
        
                <div className="mb-3">
                  <p className="font-medium text-gray-700">ทักษะ:</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {userData.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {typeof skill === 'object' 
                          ? `${skill.name} (${skill.proficiency})` 
                          : skill}
                      </span>
                    ))}
                    {userData.skills.length === 0 && (
                      <span className="text-gray-500 italic">ไม่ได้ระบุ</span>
                    )}
                  </div>
                </div>
        
                <div className="mb-3">
                  <p className="font-medium text-gray-700">ภาษาโปรแกรม:</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {userData.programmingLanguages.map((lang, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full"
                      >
                        {typeof lang === 'object' 
                          ? `${lang.name} (${lang.proficiency})` 
                          : lang}
                      </span>
                    ))}
                    {userData.programmingLanguages.length === 0 && (
                      <span className="text-gray-500 italic">ไม่ได้ระบุ</span>
                    )}
                  </div>
                </div>
        
                <div>
                  <p className="font-medium text-gray-700">เครื่องมือ:</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {userData.tools.map((tool, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded-full"
                      >
                        {typeof tool === 'object' 
                          ? `${tool.name} (${tool.proficiency})` 
                          : tool}
                      </span>
                    ))}
                    {userData.tools.length === 0 && (
                      <span className="text-gray-500 italic">ไม่ได้ระบุ</span>
                    )}
                  </div>
                </div>
              </div>
        
              {userData.projects.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h3 className="font-medium text-gray-800 border-b pb-2 mb-3">
                    โปรเจกต์ ({userData.projects.length})
                  </h3>
                  <div className="space-y-3">
                    {userData.projects.map((project, index) => (
                      <div
                        key={index}
                        className="border border-gray-200 rounded-lg p-3"
                      >
                        <h4 className="font-medium">{project.name}</h4>
                        {project.role && (
                          <p className="text-sm text-blue-600 mt-1">
                            {project.role}
                          </p>
                        )}
                        {project.description && (
                          <p className="text-sm text-gray-600 mt-1">
                            {project.description}
                          </p>
                        )}
                        {project.technologies.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {project.technologies.map((tech, i) => (
                              <span
                                key={i}
                                className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full"
                              >
                                {tech}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
        
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-800 border-b pb-2 mb-3">
                  Resume
                </h3>
                {userData.resume ? (
                  <p>{userData.resume.name}</p>
                ) : (
                  <p className="text-gray-500 italic">ไม่ได้อัปโหลด</p>
                )}
              </div>
        
              <div className="flex justify-between mt-8">
                <button
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  onClick={prevStep}
                >
                  ย้อนกลับ
                </button>
                <button
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  onClick={handleSubmit}
                >
                  บันทึกข้อมูล
                </button>
              </div>
            </div>
          );

      case 6:
        return (
          <div className="flex flex-col items-center text-center">
            <div className="mb-8 p-4 bg-green-100 rounded-full">
              <CheckCircle className="h-16 w-16 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold mb-4">ลงทะเบียนสำเร็จ!</h2>
            <p className="mb-6 text-gray-600 max-w-md">
              ขอบคุณที่ลงทะเบียนกับ AI Buddy เรียบร้อยแล้ว
              ตอนนี้คุณสามารถใช้งานได้อย่างเต็มที่
            </p>
            <button
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={() => (window.location.href = "/chat")}
            >
              เริ่มต้นสนทนากับ AI Buddy
            </button>
          </div>
        );

      default:
        return null;
    }
  };

  // Main component render
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center py-12 px-4">
      {/* Progress bar */}
      {currentStep > 0 && currentStep < 6 && (
        <div className="w-full max-w-md mb-8">
          <div className="relative pt-1">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold inline-block text-blue-600">
                ขั้นตอนที่ {currentStep} จาก 5
              </div>
              <div className="text-xs font-semibold inline-block text-blue-600">
                {Math.round((currentStep / 5) * 100)}%
              </div>
            </div>
            <div className="overflow-hidden h-2 text-xs flex rounded bg-blue-200">
              <div
                style={{ width: `${(currentStep / 5) * 100}%` }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-600"
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Registration form */}
      <div className="w-full max-w-md bg-white rounded-xl shadow-md p-6 mb-6">
        {renderStep()}
      </div>
    </div>
  );
};

export default UserRegistration;
