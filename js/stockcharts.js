Highcharts.chart('container', {

    title: {
        text: '차트 타이틀'
    },

    subtitle: {
        text: '차트 서브타이틀'
    },

    yAxis: {
        title: {
            text: 'y축 타이틀'
        }
    },

    xAxis: {
        title: {
        	text: 'x축 타이틀'
        }
    },
		
    /* 범례를 우측 세로로 정렬 */
    legend: {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'middle'
    },

    series: [{
        name: '범례 1',
        data: [43934, 52503, 57177, 69658, 97031, 119931, 137133, 154175]
    }, {
        name: '범례 2',
        data: [24916, 24064, 29742, 29851, 32490, 30282, 38121, 40434]
    }, {
        name: '범례 3',
        data: [11744, 17722, 16005, 19771, 20185, 24377, 32147, 39387]
    }, {
        name: '범례 4',
        /* series.data가 null일 경우 라인이 도식되지 않음 */
        data: [null, null, 7988, 12169, 15112, 22452, 34400, 34227]
    }, {
        name: '범례 5',
        data: [12908, 5948, 8105, 11248, 8989, 11816, 18274, 18111]
    }],
});