// canvas setup
let canvas;
let canvasWidth = 700;
let canvasHeight = 500;
let context;

// jackaloaf
let jackaloafWidth = 90;
let jackaloafHeight = 135;
let jackaloafX = canvasWidth/2 - jackaloafWidth/2;
let jackaloafY = canvasHeight/2 - jackaloafHeight/2;
let jackaloafRight;
let jackaloafLeft;

let jackaloaf = {
    img: null,
    x: jackaloafX,
    y: jackaloafY,
    width: jackaloafWidth,
    height: jackaloafHeight
}

// physics
let velocityX = 0;
let velocityY = 0; // jackaloaf jump speed
let initialVelocityY = -12; // starting velocity Y
let gravity = 0.7;

// clouds
let cloudArray = [];
let cloudWidth = 194;
let cloudHeight = 108;
let cloudImg;

// score
let score = 0;
let maxScore = 0;
let gameOver = false;

window.onload = function() {
    canvas = document.getElementById("canvas2");
    canvas.height = canvasHeight;
    canvas.width = canvasWidth;
    context = canvas.getContext("2d"); // we can draw on the canvas this way~!

    // draw jackaloaf
    // context.fillStyle = "green";
    // context.fillRect(jackaloaf.x, jackaloaf.y, jackaloaf.width, jackaloaf.height);

    // load images
    jackaloafRight = new Image();
    jackaloafRight.src = '/static/assets/sprite-sheets/jackaloaf-right.png';
    jackaloaf.img = jackaloafRight;
    jackaloafRight.onload = function(){
        context.drawImage(jackaloaf.img,jackaloaf.x,jackaloaf.y,jackaloaf.width,jackaloaf.height);
    }

    jackaloafLeft = new Image();
    jackaloafLeft.src = '/static/assets/sprite-sheets/jackaloaf-left.png';

    cloudImg = new Image();
    cloudImg.src = '/static/assets/sprite-sheets/cloud.png';

    velocityY = initialVelocityY;

    placeClouds();

    requestAnimationFrame(update);

    document.addEventListener("keydown", moveJackaloaf);
}

function update(){
    requestAnimationFrame(update);
    if (gameOver){
        return;
    }
    context.clearRect(0, 0, canvas.width, canvas.height);

    // jackaloaf
    jackaloaf.x += velocityX;
    // jackaloaf can go from the very left side of the screen to the very right, and vice versa
    if (jackaloaf.x > canvasWidth){
        jackaloaf.x = -80;
    }
    else if (jackaloaf.x + jackaloaf.width < 0){
        jackaloaf.x = canvasWidth;
    }

    velocityY += gravity;
    jackaloaf.y += velocityY;
    if (jackaloaf.y > canvas.height){
        gameOver = true;
    }
    context.drawImage(jackaloaf.img,jackaloaf.x,jackaloaf.y,jackaloaf.width,jackaloaf.height);

    // clouds
    for (let i = 0; i < cloudArray.length; i++){
        let cloud = cloudArray[i];
        if (velocityY < 0 && jackaloaf.y < canvasHeight*3/4) {
            cloud.y -= initialVelocityY; // slide cloud down
        }
        if (detectCollision(jackaloaf, cloud) && velocityY >= 0){
            velocityY = initialVelocityY; // jump
        }
        context.drawImage(cloud.img, cloud.x, cloud.y, cloud.width, cloud.height);
    }

    // clear clouds and add new clouds
    while (cloudArray.length > 0 && cloudArray[4].y >= canvasHeight) {
        cloudArray.shift(); // removes first element from the array
        newCloud();
    }

    // score
    updateScore();
    context.fillStyle = "black";
    context.font = "50px Trebuchet MS";
    context.fillText('Score: ' + score, 10, 45);

    // game over
    if (gameOver){
        context.font = "35px Trebuchet MS";
        context.fillText("You've gained " + Math.trunc(score/20) + " Lamocoins!", 125, 400);
        context.font = "31px Trebuchet MS";
        context.fillText("Press 'Space' to Restart!", 190, 450);
    }
}

function moveJackaloaf(e) {
    if (e.code == "ArrowRight" || e.code == "KeyD") {
        // move right
        velocityX = 4;
        jackaloaf.img = jackaloafRight;
    }
    else if (e.code == "ArrowLeft" || e.code == "KeyA") {
        // move left
        velocityX = -4;
        jackaloaf.img = jackaloafLeft;
    }
    else if (e.code == "Space" && gameOver) {
        // reset
        jackaloaf = {
            img: jackaloafRight,
            x: jackaloafX,
            y: jackaloafY,
            width: jackaloafWidth,
            height: jackaloafHeight
        }

        velocityX = 0;
        velocityY = initialVelocityY;
        score = 0;
        maxScore = 0;
        gameOver = false;
        placeClouds();
    }
}

function placeClouds() {
    cloudArray = [];

    // starting clouds
    let cloud = {
        img: cloudImg,
        x: canvasWidth/2,
        y: canvasHeight - 120,
        width: cloudWidth,
        height: cloudHeight
    }

    cloudArray.push(cloud);

    for (let i = 0; i < 6; i++) {
        let randomX = Math.floor(Math.random() * canvasWidth*3/4); // (0-1) * canvasWidth*3/4
        let cloud = {
            img: cloudImg,
            x: randomX,
            y: canvasHeight - 190*i - 300,
            width: cloudWidth,
            height: cloudHeight
        }

        cloudArray.push(cloud);
    }
}

function newCloud() {
    let randomX = Math.floor(Math.random() * canvasWidth*3/4); // (0-1) * canvasWidth*3/4
    let cloud = {
        img: cloudImg,
        x: randomX,
        y: -cloudHeight,
        width: cloudWidth,
        height: cloudHeight
    }

    cloudArray.push(cloud);
}

function detectCollision(a,b) {
    return a.x < b.x + b.width && // a's top left corner doesn't reach b's top left corner
           a.x + a.width > b.x && // a's top right corner passes b's top left corner
           a.y < b.y + b.height && // a's top left corner doesn't reach b's bottom left corner
           a.y + a.height > b.y;  // a's bottom left corner passes b's top left corner
}

function updateScore() {
    let points = Math.floor(50*Math.random()); // (0-1)* 50 --> (0-50)
    if (velocityY < 0){
        // negative going up
        maxScore += points;
        if (score < maxScore) {
            score = maxScore;
        }
    }
    else if(velocityY >= 0){
        maxScore -= points;
    }
}