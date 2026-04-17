export default {
  root: "src",
  title: "Quantum Stability Monitor",
  pages: [
    {name: "Overview", path: "/"},
    {
      name: "Platforms",
      pages: [
        {name: "AQT IBEX", path: "/aqt"},
        {name: "IonQ Aria-1", path: "/ionq"},
        {name: "Rigetti Ankaa-3", path: "/rigetti"},
      ]
    },
    {name: "Methodology", path: "/about"},
    {name: "About Insight Softmax", path: "/about-isc"},
  ],
  head: '<link rel="stylesheet" href="/theme.css">',
  footer: 'Quantum Stability Monitor — longitudinal QPU benchmarking by <a href="https://insightsoftmax.com/" target="_blank" rel="noopener">Insight Softmax</a>',
};
