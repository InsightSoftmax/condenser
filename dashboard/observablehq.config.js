export default {
  root: "src",
  title: "Quantum Stability Monitor",
  pages: [
    {name: "Overview", path: "/"},
    {
      name: "Platforms",
      pages: [
        {name: "Rigetti Ankaa-3", path: "/rigetti"},
        {name: "AQT IBEX", path: "/aqt"},
        {name: "IonQ Aria-1", path: "/ionq"},
        {name: "IBM Brisbane", path: "/ibm"},
      ]
    },
    {name: "Methodology", path: "/about"},
  ],
  head: '<link rel="stylesheet" href="/theme.css">',
  footer: "Quantum Stability Monitor — longitudinal QPU benchmarking by Insight Softmax",
};
