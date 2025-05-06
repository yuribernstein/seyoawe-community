const wizardConfig = {
  steps: [
    {
      id: "approval",
      type: "junction",
      question: " Approve Certificate Request?",
      iconName: "Certificate",
      options: [
        { label: "approve", nextStep: "reason_approve" },
        { label: "deny", nextStep: "reason_deny" }
      ]
    },
    {
      id: "reason_approve",
      type: "dropdown",
      label: " Reason",
      options: [
        "I like it",
        "I want it",
        "I need it",
        "I care",
        "I understand it",
        "I know",
        "I have time"
      ],
      iconName: "dataCenter",
      nextStep: "comments"
    },
    {
      id: "reason_deny",
      type: "dropdown",
      label: " Reason",
      options: [
        "I don't like it",
        "I don't want it",
        "I don't need it",
        "I don't care",
        "I don't understand it",
        "I don't know",
        "I don't have time"
      ],
      iconName: "dataCenter",
      nextStep: "comments"
    },
    {
      id: "comments",
      type: "textbox",
      iconName: "Jira",
      label: " Add more details",
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


