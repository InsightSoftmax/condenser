export default {
  root: "src",
  title: "Quantum Stability Monitor",
  pages: [
    {name: "Overview", path: "/"},
    {
      name: "Platforms",
      pages: [
        {name: "AQT IBEX", path: "/aqt"},
        {name: "IBM Brisbane", path: "/ibm"},
        {name: "IonQ Aria-1", path: "/ionq"},
        {name: "IonQ Forte-1", path: "/ionq-forte"},
        {name: "Rigetti Cepheus-1-108Q", path: "/rigetti"},
      ]
    },
    {name: "Methodology", path: "/about"},
    {name: "About Insight Softmax", path: "/about-isc"},
    {name: "Contact", path: "/contact"},
  ],
  head: '<link rel="stylesheet" href="/theme.css">',
  footer: 'Quantum Stability Monitor — longitudinal QPU benchmarking by <a href="https://insightsoftmax.com/" target="_blank" rel="noopener">Insight Softmax</a>',
};
