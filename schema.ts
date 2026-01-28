import { z } from "zod";

export const GetGradesSchema = z.object({
  query: z.string().describe("The student's Name (e.g. 'Harsh') OR Matriculation ID (e.g. 's1001')"),
});

export const GetScheduleSchema = z.object({
  course_name: z.string().describe("The course name (e.g., Wirtschaftsinformatik)"),
});

export const GetProfessorInfoSchema = z.object({
    prof_name: z.string().describe("The name of the professor (e.g. 'Kessel')"),
});

export const GetAllProfessorsSchema = z.object({});

export const GetProfessorForModuleSchema = z.object({
    module_name: z.string().describe("The name of the module or a keyword from it (e.g., 'Web Engineering', 'web eng')."),
});

export const QueryAcademicDataSchema = z.object({
    student_name: z.string().optional().describe("The name of the student."),
    professor_name: z.string().optional().describe("The name of the professor."),
    course_name: z.string().optional().describe("The name of the course."),
});

export const GetEventsSchema = z.object({}).describe("Get a list of all upcoming university events.");