const todayDate = new Date();
let day = String(todayDate.getDate()).padStart(2, '0');
let month = String(todayDate.getMonth() + 1).padStart(2, '0');
let year = todayDate.getFullYear();
let currDate = `${year}-${month}-${day}`;
document.getElementById("userDate").value = currDate;
