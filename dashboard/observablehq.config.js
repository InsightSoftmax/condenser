export default {
  root: "src",
  title: "Condenser",
  pages: [
    {name: "Overview", path: "/"},
    {
      name: "Platforms",
      pages: [
        {name: "Rigetti Ankaa-3", path: "/rigetti"},
        {name: "AQT ibex", path: "/aqt"},
        {name: "IonQ Aria-1", path: "/ionq"},
      ]
    },
    {name: "Methodology", path: "/about"},
  ],
  head: '<link rel="stylesheet" href="/theme.css">',
  footer: "Condenser — longitudinal quantum stability benchmarking by Insight Softmax",
};
