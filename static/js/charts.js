const sessions = window.studentSessions || [];
if (sessions.length) {
  const labels = sessions.map(s => s.date).reverse();
  const scores = sessions.map(s => s.score).reverse();
  makeChart('scoreTrend',{type:'line',data:{labels,datasets:[{label:'Score',data:scores,borderColor:'#1f9fae',tension:.3}]}});
  makeChart('practiceFreq',{type:'bar',data:{labels:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],datasets:[{data:[1,2,1,3,2,1,2],backgroundColor:'#123a66'}]}});
  makeChart('topicPerf',{type:'radar',data:{labels:['Arthritis','Replacement','Sports','Spine'],datasets:[{data:[78,72,81,69],backgroundColor:'rgba(31,159,174,.2)',borderColor:'#1f9fae'}]}});
  makeChart('confTrend',{type:'line',data:{labels,datasets:[{label:'Confidence',data:scores.map(s=>Math.min(100,s+5)),borderColor:'#123a66'}]}});
}
