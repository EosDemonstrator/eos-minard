async function BADloadRunData(name) {
    let file_path;
    console.log(name);
    switch(name) {
      case "137cs_run90":
        file_path = "{{ url_for('static', 'datasets/137cs_run90-996.json }}";
        console.log("I AM HERE");
        break;
    }
    try {
      console.log(file_path);  
      const response = await fetch(file_path);
        if (response.ok) {
          const jsonResponse = await response.json();
          const validJsonString = jsonResponse.name.replace(/'/g, '"');
          const data = JSON.parse(validJsonString);
          console.log(data);
          processData(data);
          console.log('Run data processed!');
        } else {
          console.log('Error: ' + response.status);
        }
    } catch (error) {
        console.error('Run data request failed: ', error);
    }
}

function metricsRequest() {
    const values = $("#timeSlider").slider("values");
    const startHours = Math.floor(values[0] / 60);
    const startMins = values[0] % 60;
    const startTime = `${String(startHours).padStart(2, '0')}:${String(startMins).padStart(2, '0')}`;

    const endHours = Math.floor(values[1] / 60);
    const endMins = values[1] % 60;
    const endTime = `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`;
    const myDate = document.getElementById("userDate").value;

    //alert(`Start Time: ${startTime} UTC\nEnd Time: ${endTime} UTC\nDate: ${myDate}\nJSON Query: expr=e_gtid&start=${myDate}T${startHours}%3A${startMins}%3A00.000Z&stop=${myDate}T${endHours}%3A${endMins}%3A00.000Z&step=1&now=${myDate}T${endHours}%3A${endMins}%3A00.000Z`);

    var xhr = new XMLHttpRequest();
    xhr.open('GET', 'event.txt', true);
    //xhr.open('GET', 'http://eos-daq.localdomain/metric?expr=e_gtid&start=2024-07-01T17%3A20%3A00.000Z&stop=2024-07-01T17%3A50%3A00.000Z&step=1&now=2024-07-01T17%3A50%3A00.000Z', true);
    console.log('Made request');
    xhr.onload = function() {
        if(this.status == 200) {
            var jsonResponse = JSON.parse(this.responseText);
            // Replace single quotes with double quotes to make it a valid JSON string
            var validJsonString = jsonResponse.name.replace(/'/g, '"');
            // Parse the valid JSON string to a JavaScript object
            var data = JSON.parse(validJsonString);
            console.log(data);
        } else {
            console.error('Error: ' + this.status);
        }
    };
    xhr.onerror = function() {
        console.error('Request failed');
    };
    xhr.send();
}

// The range of colors in getJetColorString is 0.125-0.875, from fully blue to fully red.
// The scaling of raw data makes the maximum charge for each run (255,0,0)

let dataStruct =
    { name: "live_data",
      q_scale: 1.00,
      t_scale: 1.00,
    };

function toggleData() {
    dataStruct.name = "137cs_run90";
    dataStruct.t_scale = 200.0;
    dataStruct.q_scale = 1/(parseInt(document.getElementById("upperCharge").innerText)*0.875)*1e5;
    console.log('Getting local data...');
}

function makeGradient() {
      const c = document.getElementById("grad");
      c.style.border = "1px solid grey;";
      const ctx = c.getContext("2d");

      // Create vertical linear gradient
      const grad = ctx.createLinearGradient(0, 0, 0, 210);
      grad.addColorStop(0, "red"); // Top color
      grad.addColorStop(0.25, "yellow");
      grad.addColorStop(0.5, "green");
      grad.addColorStop(0.75, "cyan");
      grad.addColorStop(1, "blue"); // Bottom color

      // Fill rectangle with gradient
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, c.width, c.height);

      ctx.fillStyle = "black";
      ctx.font = "12px Arial";
      ctx.textAlign = "right";
      const scaleStep = 50;
      for (let i = 0; i <= 300; i += scaleStep) {
        const y = c.height - (i / 300) * 220;
        ctx.fillText(i, 25, y);
        ctx.beginPath();
        ctx.moveTo(26, y);
        ctx.lineTo(40, y);
        ctx.stroke();
      }
}
