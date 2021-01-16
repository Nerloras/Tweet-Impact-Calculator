const formatter = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 4,      
    maximumFractionDigits: 4,
});

$('#setForm').submit(function(e) {
  $.ajax({
      data : {
          tweet : $('#tweetInput').val(),
          stock : $('#stockInput').val()
      },
      type : 'POST',
      url : '/process'
  })
  .done(function(data) {
      if (data.error) {
          $('#noStock').text(data.error).show();
          $('#successAlert').hide();
      }
      else {
        $('#tweetInfo').css('display', '');
        $('#tweetBox').html(data.html).show();
        $('#tweetPoster').text(data.account).show();
        $('#tweetDate').text(data.date).show();
        
        
    
        finalData = JSON.parse(data.stockData), data.stockInfo
        $('#stockOpen').text(data.dOpen).show();
        $('#stockHigh').text(data.dHigh).show();
        $('#stockLow').text(data.dLow).show();
        $('#stockClose').text(data.dClose).show();
        $('#stockImpact').text(formatter.format(data.dImpact)).show();
        $('#stockPercent').text(data.dPercent).show();

        let sImpact = document.getElementById("stockImpact");
        sImpact.classList.add(data.outcome);
        let sPercent = document.getElementById("stockPercent");
        sPercent.classList.add(data.outcome);
        
        var priceData = [];
        var dates = [];
        var priceOpen = [];
        var priceHigh = [];
        var priceLow = [];
        var title = data.stockInfo.shortName  + " (" + data.stockInfo.symbol + ") - " + numeral(data.stockInfo.ask).format('$0,0.00');

        for(var i in finalData.Close){
            var dt = i.slice(0,i.length-3);
            var dateString = moment.unix(dt).format("DD/MM");
            var close = finalData.Close[i];
            if(close != null){
                priceData.push(finalData.Close[i]);
                priceOpen.push(finalData.Open[i]);
                priceHigh.push(finalData.High[i]);
                priceLow.push(finalData.Low[i]);
                dates.push(dateString);
            }
        }
        
    Highcharts.chart('chart_container', {
    title: {
        text: title
    },
    xAxis: {
        categories: dates,
    },
    yAxis: {
        type: 'logarithmic',
        labels: {
            format: '{value:.2f}'
        }
    },
    tooltip: {
        pointFormat: "Value: {point.y:.2f}"
    },
    labels: {
        items: [{
            style: {
                left: '50px',
                top: '18px',
                color: ( // theme
                    Highcharts.defaultOptions.title.style &&
                    Highcharts.defaultOptions.title.style.color
                ) || 'black'
            }
        }]
    },
    series: [{
        type: 'column',
        name: 'Opening price',
        data: priceOpen
    }, {
        type: 'column',
        name: 'Lowest price',
        data: priceLow
    }, {
        type: 'column',
        name: 'Highest price',
        data: priceHigh
    }, {

        type: 'spline',
        name: 'Closing price',
        data: priceData,
        dataLabels: {
            enabled: true,
            formatter: function () {
                return Highcharts.numberFormat(this.y,2);
            }
        },
        marker: {
            lineWidth: 2,
            lineColor: Highcharts.getOptions().colors[3],
            fillColor: 'white'
        }
    }]
    });

      }

  });
  e.preventDefault();
});