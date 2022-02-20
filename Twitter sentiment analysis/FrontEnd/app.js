var btnTranslate = document.querySelector("#btn-translate");
var txtInput = document.querySelector("#txt-input");
var txtOutput = document.querySelector("#txt-output");
const serverUrl = "https://sentimental-analysis33.herokuapp.com/getSentiment";

function getTranslatedUrl(text) {
  return serverUrl + "?text=" + text;
}

function errorHandler(error) {
  console.log("Error occured: ", error);
  alert("Try again after sometime!");
}
var myHeaders = new Headers();
myHeaders.append("Content-Type", "application/json");
var raw = JSON.stringify({
    "keyword": "#SharkTankIndia",
    "tweets": "100"
  });
var requestOptions = {
  method: "POST",
  headers: myHeaders,
  body: raw,
  redirect: "follow",
};

btnTranslate.addEventListener("click", () => {
  var inputText = txtInput.value;

  fetch("https://sentimental-analysis33.herokuapp.com/getSentiment", requestOptions)
  .then(response => response.json())
  .then(result => {
      txtOutput.innerText = result.final_sentiment
  })
  
});
