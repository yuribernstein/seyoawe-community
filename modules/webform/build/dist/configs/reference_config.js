const wizardConfig = {
    steps: [
      {
        id: "start",
        type: "junction",
        question: " Select customer type",
        iconName: "searchCustomer",
        options: [
          { label: "Regular", nextStep: "regular_customer" },
          { label: "Managed", nextStep: "managed_domain" }
        ]
      },
      {
        id: "regular_customer",
        type: "searchable-dropdown",
        label: " Customer",
        apiFetch: "http://localhost:8080/api/customers",
        responsePath: "",
        iconName: "searchCustomer",
        nextStep: "regular_data_center"
      },
      {
        id: "regular_data_center",
        type: "dropdown",
        label: " Data Center",
        options: [
          "DC1",
          "DC2",
          "DC3",
          "DC4"
        ],
        iconName: "dataCenter",
        nextStep: "customer_email"
      },
      {
        id: "customer_email",
        type: "input",
        label: " Email",
        iconName: "Website",
        nextStep: "customer_team_members"
      },
      {
        id: "customer_team_members",
        type: "multiinput",
        label: " Add team members",
        max_inputs: 5, // Limits number of inputs
        iconName: "searchCustomer",
        nextStep: "jira"
      },
      {
        id: "jira",
        type: "checkbox",
        iconName: "Jira",
        label: " Need a new ticket?",
        type: "junction",
        options: [
          { label: "Yes", nextStep: "ticket_description" },
          { label: "No", nextStep: "add_ticket_id" }
        ]
      },
      {
        id: "add_ticket_id",
        type: "input",
        iconName: "Jira",
        label: " Ticket ID",
        nextStep: "submit"
      },
      {
        id: "ticket_description",
        type: "textbox",
        iconName: "Jira",
        label: " Ticket Description",
        nextStep: "submit"
      },
      {
        id: "submit",
        label: "Submit ?",
        headers: { "Content-Type": "application/json" },
        type: "submit"
      }
    ]
  };
  
  export default wizardConfig;
  
  
  