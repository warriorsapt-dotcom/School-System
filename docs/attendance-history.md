# Student attendance history

Teachers can open **My Students**, then select **Attendance History** beside a student. The same button is available in **Attendance** after selecting a class and loading its students. Administrators can use the attendance register entry point too.

The window lists saved records with the newest date first: date, class, status, term, teacher who marked attendance, and remarks. Use **From**, **To**, and **Status**, then **Apply filters** to narrow the records. Date boundaries are inclusive. **Reset** clears the filters; **Previous** and **Next** navigate all matching records.

An empty result means no saved records match the filters. Days without a record are not treated as absences. This window is read-only and does not change attendance being marked in the register.

The history endpoint allows administrators and teachers assigned as a subject teacher or class teacher of the student's current class. It includes the student's older records, including records from previous classes. Unrelated teachers cannot open that student's history endpoint.

This update needs no database migrations or additional dependencies. Pull the update, restart Django, and refresh the browser to load the updated JavaScript.
