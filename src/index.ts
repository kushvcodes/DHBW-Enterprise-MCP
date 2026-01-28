import express from "express";
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import cors from "cors";
import { 
    GetGradesSchema,
    GetScheduleSchema,
    GetProfessorInfoSchema,
    GetAllProfessorsSchema,
    GetProfessorForModuleSchema,
    QueryAcademicDataSchema,
    GetEventsSchema
} from "./schema.js";
import db from "./db.json" with { type: "json" };

const app = express();
app.use(cors());

const server = new McpServer({ name: "dhbw-academic-assistant", version: "4.3.0" });

// --- HELPER FUNCTIONS (NOW MORE ROBUST) ---

function normalize(str: string): string {
    if (!str) return "";
    return str.toLowerCase().trim().replace(/[\s\.-]/g, '');
}

function findStudentId(query: string): string | null {
  console.log(`[DEBUG] findStudentId received query: "${query}"`);
  const normalizedQ = normalize(query);
  console.log(`[DEBUG] Normalized query: "${normalizedQ}"`);

  // 1. Direct ID match
  if (db.students[normalizedQ as keyof typeof db.students]) {
    console.log(`[DEBUG] Found direct ID match: "${normalizedQ}"`);
    return normalizedQ;
  }

  // 2. Exact normalized name match
  for (const [id, student] of Object.entries(db.students)) {
    const normalizedStudentName = normalize(student.name);
    if (normalizedStudentName === normalizedQ) {
      console.log(`[DEBUG] Found exact name match. Returning ID: "${id}"`);
      return id;
    }
  }
  
  // 3. Substring match
  for (const [id, student] of Object.entries(db.students)) {
    const normalizedStudentName = normalize(student.name);
    if (normalizedStudentName.includes(normalizedQ)) {
      console.log(`[DEBUG] Found substring name match. Returning ID: "${id}"`);
      return id;
    }
  }

  console.log(`[DEBUG] No student found for query: "${query}"`);
  return null;
}

function findProfessorId(query: string): string | null {
    const normalizedQ = normalize(query);
    for (const [id, prof] of Object.entries(db.professors)) {
      if (normalize(prof.name).includes(normalizedQ)) {
        return id;
      }
    }
    return null;
}

function findModule(query: string): { id: string, name: string } | null {
    const normalizedQ = normalize(query);
    for (const studentId in db.grades) {
        for (const grade of db.grades[studentId as keyof typeof db.grades]) {
            if (normalize(grade.module).includes(normalizedQ)) {
                return { id: grade.module_id, name: grade.module };
            }
        }
    }
    return null;
}


// --- INDIVIDUAL, SIMPLE TOOLS ---

server.tool(
  "get_student_grades",
  "Search grades for a single student by their Name OR ID.",
  GetGradesSchema.shape,
  async ({ query }) => {
    const studentId = findStudentId(query);
    if (!studentId) {
      return { content: [{ type: "text", text: `Student '${query}' not found.` }] };
    }
    const studentInfo = db.students[studentId as keyof typeof db.students];
    const grades = db.grades[studentId as keyof typeof db.grades] || [];

    // Pre-format the response on the server
    let formattedResponse = `**Grades for ${studentInfo.name} (${studentId})**\n\n`;
    if (grades.length === 0) {
        formattedResponse += "No grades found for this student.";
    } else {
        grades.forEach(grade => {
            const profInfo = db.professors[grade.prof_id as keyof typeof db.professors];
            formattedResponse += `* **Module:** ${grade.module}\n`;
            formattedResponse += `  - **Grade:** ${grade.grade}\n`;
            formattedResponse += `  - **Professor:** ${profInfo ? profInfo.name : 'N/A'}\n`;
        });
    }

    return { content: [{ type: "text", text: formattedResponse }] };
  }
);

server.tool(
  "get_schedule",
  "Get the lecture schedule for a specific course.",
  GetScheduleSchema.shape,
  async ({ course_name }) => {
    console.log(`[DEBUG] get_schedule called with: "${course_name}"`);
    const normalizedCourse = Object.keys(db.schedule).find(k => normalize(k) === normalize(course_name));
    console.log(`[DEBUG] found normalized key: "${normalizedCourse}"`);
    
    if (!normalizedCourse) {
        return { content: [{ type: "text", text: `Course '${course_name}' not found.`}] };
    }
    const schedule = db.schedule[normalizedCourse as keyof typeof db.schedule] || [];
    const detailedSchedule = schedule.map(lecture => {
        const profInfo = db.professors[lecture.prof_id as keyof typeof db.professors];
        return { ...lecture, professor_name: profInfo ? profInfo.name : 'Unknown' };
    });
    return { content: [{ type: "text", text: JSON.stringify(detailedSchedule) }] };
  }
);

server.tool(
    "get_all_professors",
    "Returns a list of all professors in the database.",
    GetAllProfessorsSchema.shape,
    async () => {
        const professorNames = Object.values(db.professors).map(p => p.name);
        return { content: [{ type: "text", text: JSON.stringify(professorNames) }] };
    }
);

server.tool(
    "get_professor_for_module",
    "Find the professor who teaches a specific module.",
    GetProfessorForModuleSchema.shape,
    async ({ module_name }) => {
        const moduleInfo = findModule(module_name);
        if (!moduleInfo) return { content: [{ type: "text", text: `Module '${module_name}' not found.` }] };

        let profId: string | null = null;
        for (const studentId in db.grades) {
            const grade = (db.grades[studentId as keyof typeof db.grades] || []).find(g => g.module_id === moduleInfo.id);
            if (grade) {
                profId = grade.prof_id;
                break;
            }
        }

        if (profId) {
            const profInfo = db.professors[profId as keyof typeof db.professors];
            return { content: [{ type: "text", text: JSON.stringify({ module: moduleInfo.name, professor: profInfo.name }) }] };
        } else {
            return { content: [{ type: "text", text: `Could not determine professor for module '${moduleInfo.name}'.` }] };
        }
    }
);

server.tool(
    "get_professor_info",
    "Get office and email for a professor by name.",
    GetProfessorInfoSchema.shape,
    async ({ prof_name }) => {
      const profId = findProfessorId(prof_name);
      if (!profId) {
        return { content: [{ type: "text", text: `Professor '${prof_name}' not found.` }] };
      }
      const info = db.professors[profId as keyof typeof db.professors];
      return { content: [{ type: "text", text: JSON.stringify(info) }] };
    }
);

server.tool(
    "get_events",
    "Get a list of all upcoming university events.",
    GetEventsSchema.shape,
    async () => {
        return { content: [{ type: "text", text: JSON.stringify(db.events) }] };
    }
);


// --- ADVANCED INTERSECTIONAL TOOL ---

server.tool(
    "query_academic_data",
    "Answers complex queries by combining student, professor, and/or course information. Use for queries like 'What courses does professor X teach student Y?'",
    QueryAcademicDataSchema.shape,
    async ({ student_name, professor_name, course_name }) => {
        let results: any[] = [];
        let queryDescription = "Query Results";

        const studentId = student_name ? findStudentId(student_name) : null;
        const profId = professor_name ? findProfessorId(professor_name) : null;

        if (student_name && !studentId) return { content: [{ type: "text", text: `Student '${student_name}' not found.` }] };
        if (professor_name && !profId) return { content: [{ type: "text", text: `Professor '${professor_name}' not found.` }] };

        if (studentId) {
            const studentInfo = db.students[studentId as keyof typeof db.students];
            queryDescription = `Results for student: ${studentInfo.name}`;
            results = (db.grades[studentId as keyof typeof db.grades] || []).map(grade => {
                const profInfo = db.professors[grade.prof_id as keyof typeof db.professors];
                return { ...grade, professor_name: profInfo.name };
            });
            if (profId) {
                queryDescription += ` and professor: ${db.professors[profId as keyof typeof db.professors].name}`;
                results = results.filter(grade => grade.prof_id === profId);
            }
        } else if (profId) {
            const profInfo = db.professors[profId as keyof typeof db.professors];
            queryDescription = `Courses taught by professor: ${profInfo.name}`;
            const taughtModules = new Set<string>();
            Object.values(db.grades).flat().forEach(grade => {
                if (grade.prof_id === profId) {
                    taughtModules.add(grade.module);
                }
            });
            results = Array.from(taughtModules);
        } else if (course_name) {
            queryDescription = `Information for course: ${course_name}`;
            const courseKey = Object.keys(db.courses).find(k => normalize(k).includes(normalize(course_name)));
            if(courseKey) results = [db.courses[courseKey as keyof typeof db.courses]];
        }

        return { content: [{ type: "text", text: JSON.stringify({ queryDescription, results }) }] };
    }
);


// --- RESOURCES ---
server.resource("syllabus", new ResourceTemplate("dhbw://syllabus/{code}", { 
    list: async () => ({
      resources: Object.keys(db.syllabi).map(code => ({ uri: `dhbw://syllabus/${code}`, name: code, description: `Syllabus for ${code}` }))
    })
  }),
  async (uri, { code }) => {
    const text = db.syllabi[code as keyof typeof db.syllabi] || "Not found.";
    return { contents: [{ uri: uri.href, mimeType: "text/plain", text }] };
  }
);

server.resource("news", new ResourceTemplate("dhbw://news/{article_id}", {
    list: async () => ({
      resources: Object.entries(db.news).map(([id, article]) => ({ uri: `dhbw://news/${id}`, name: id, description: article.headline }))
    })
  }),
  async (uri, { article_id }) => {
    const article = db.news[article_id as keyof typeof db.news];
    return { contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(article || null) }] };
  }
);

server.resource("publications", new ResourceTemplate("dhbw://publications/{prof_id}", {
    list: async () => ({
      resources: Object.keys(db.publications).map(prof_id => ({ uri: `dhbw://publications/${prof_id}`, name: prof_id, description: `Publications for ${db.professors[prof_id as keyof typeof db.professors].name}` }))
    })
  }),
  async (uri, { prof_id }) => {
    const pubs = db.publications[prof_id as keyof typeof db.publications];
    return { contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(pubs || []) }] };
  }
);

// --- TRANSPORT ---
let transport: SSEServerTransport | null = null;
app.get("/sse", async (req, res) => { transport = new SSEServerTransport("/messages", res); await server.connect(transport); });
app.post("/messages", async (req, res) => { if (transport) await transport.handlePostMessage(req, res); });

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`✅ DHBW Enterprise Server running on port ${PORT}`));
