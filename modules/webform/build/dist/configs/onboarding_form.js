export const form = {
    title: "New Employee Onboarding",
    description: "Please fill out the onboarding details and approve or reject the process.",
    steps: [
      {
        id: "employee_info",
        title: "Employee Details",
        fields: [
          {
            id: "employee_name",
            label: "Employee Name",
            type: "text",
            required: true,
          },
          {
            id: "employee_email",
            label: "Employee Email",
            type: "email",
            required: true,
          }
        ]
      },
      {
        id: "it_preferences",
        title: "IT Provisioning",
        fields: [
          {
            id: "department",
            label: "Department",
            type: "select",
            required: true,
            options: ["Engineering", "Sales", "Marketing", "HR", "Finance"]
          },
          {
            id: "role",
            label: "Role",
            type: "text",
            required: true,
          },
          {
            id: "device_preference",
            label: "Preferred Device",
            type: "select",
            options: ["MacBook Pro", "Windows Laptop", "Linux Workstation"],
            required: true,
          }
        ]
      },
      {
        id: "final_step",
        title: "Final Decision",
        fields: [
          {
            id: "approval_decision",
            label: "Do you approve this onboarding?",
            type: "approval", // Special type for built-in approval status
            required: true,
          },
          {
            id: "notes",
            label: "Additional Notes (Optional)",
            type: "textarea",
            required: false,
          }
        ]
      }
    ]
  };
  