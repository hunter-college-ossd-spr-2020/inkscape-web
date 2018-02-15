
$(document).ready(function() {
    nv.addGraph(function() {
      var chart = nv.models.pieChart()
	  .x(function(d) { return d.label })
	  .y(function(d) { return d.value })
	  .showLabels(true);

	d3.select("svg#pie")
	    .datum(exampleData())
	    .transition().duration(350)
	    .call(chart);

      return chart;
    });

    nv.addGraph(function() {
	var chart = nv.models.stackedAreaChart()
		      .margin({right: 100})
		      .x(function(d) { return d[0] })   //We can modify the data accessor functions...
		      .y(function(d) { return d[1] })   //...in case your data is formatted differently.
		      .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
		      .rightAlignYAxis(true)      //Let's move the y-axis to the right side.
		      //.transitionDuration(500)
		      .showControls(true)       //Allow user to choose 'Stacked', 'Stream', 'Expanded' mode.
		      .clipEdge(true);

	//Format x-axis labels with custom function.
	chart.xAxis
	    .tickFormat(function(d) { 
	      return d3.time.format('%x')(new Date(d)) 
	});

	chart.yAxis
	    .tickFormat(d3.format(',.2f'));

	d3.select('svg#stack')
	  .datum(chart_data)
	  .call(chart);

	nv.utils.windowResize(chart.update);

	return chart;
    });
});

function exampleData() {
  return  [
      { 
        "label": "One",
        "value" : 29.765957771107
      } , 
      { 
        "label": "Two",
        "value" : 0
      } , 
      { 
        "label": "Three",
        "value" : 32.807804682612
      } , 
      { 
        "label": "Four",
        "value" : 196.45946739256
      } , 
      { 
        "label": "Five",
        "value" : 0.19434030906893
      } , 
      { 
        "label": "Six",
        "value" : 98.079782601442
      } , 
      { 
        "label": "Seven",
        "value" : 13.925743130903
      } , 
      { 
        "label": "Eight",
        "value" : 5.1387322875705
      }
    ];
}
