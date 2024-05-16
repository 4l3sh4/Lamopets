// canvas setup
const canvas = document.getElementById('canvas1');
const ctx = canvas.getContext('2d');
canvas.width = 800;
canvas.height = 500;

let score = 0;
let gameFrame = 0;
ctx.font = '50px Trebuchet MS';
let gameSpeed = 1;
let gameOver = false;

// mouse interactivity
// detects the mouse's movement and stuff
// REMINDER TO SELF: change this to arrow keys movement in the future if possible
let canvasPosition = canvas.getBoundingClientRect();

const mouse = {
    x: canvas.width/2,
    y: canvas.height/2,
    click: false
}

canvas.addEventListener('mousedown', function(event){
    mouse.click = true;
    mouse.x = event.x;
    mouse.y = event.y;
});
canvas.addEventListener('mouseup', function(){
    mouse.click = false;
})

// player
const playerLeft = new Image();
playerLeft.src = '/static/assets/sprite-sheets/fish-player-sheet.png'
const playerRight = new Image();
playerRight.src = '/static/assets/sprite-sheets/fish-player-sheet-flipped.png'

class Player {
    constructor(){
        this.x = canvas.width;
        this.y = canvas.height/2;
        this.radius = 50;
        this.angle = 0;
        this.frameX = 0;
        this.frameY = 0;
        this.frame = 0;
        this.spriteWidth = 270;
        this.spriteHeight = 200;
    }
    update(){
        const dx = this.x - mouse.x;
        const dy = this.y - mouse.y;
        // change these values if you want the fishy to move slower/faster
        if (mouse.x != this.x) {
            this.x -= dx/20;
        }
        if (mouse.y != this.y) {
            this.y -= dy/20;
        }
        // this will play every 5 frames
        if (gameFrame % 15 == 0){
            this.frameX++;
            if (this.frameX >= 3) this.frameX = 0;
        }
    }
    draw(){
        if (mouse.click) {
            ctx.linewidth = 0.2;
            ctx.beginPath();
            ctx.moveTo(this.x, this.y);
            /* ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke(); */
        }
        /* ctx.fillStyle = 'red';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
        ctx.fillRect(this.x,this.y,this.radius,10) */

        ctx.save();
        ctx.translate(this.x, this.y);
        if (this.x >= mouse.x){
            ctx.drawImage(playerLeft, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, 0 - 40, 0 - 35, this.spriteWidth/3, this.spriteHeight/3);
        } else {
            ctx.drawImage(playerRight, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, 0 - 40, 0 - 35, this.spriteWidth/3, this.spriteHeight/3);
        }
        ctx.restore();
    }
}
const player = new Player();

// baby fish
const babyLeft = new Image();
babyLeft.src = '/static/assets/sprite-sheets/fish-baby-sheet.png'
const babyRight = new Image();
babyRight.src = '/static/assets/sprite-sheets/fish-baby-sheet-flipped.png'

const babyArray = [];
class babyFish {
    constructor(){
        this.random = Math.random() <= 0.5 ? 'spawn1' : 'spawn2';
        if (this.random == 'spawn1'){
            this.x = canvas.width + 100;
        } else {
            this.x = canvas.width - 900;
        }
        this.y = Math.random() * (canvas.height - 150) + 90;
        this.radius = 30;
        this.speed = Math.random() * 2 + 2;
        this.frameX = 0;
        this.frameY = 0;
        this.frame = 0;
        this.spriteWidth = 175;
        this.spriteHeight = 125;
        this.distance;
        this.counted = false;
        // this is called a 'ternary operator'! it's basically a one-line if-else statement. very cool!
        this.sound = Math.random() <= 0.5 ? 'sound1' : 'sound2';
    }
    update(){
        if (this.random == 'spawn1'){
            this.x -= this.speed;
        } else {
            this.x += this.speed;
        }
        const dx = this.x - player.x;
        const dy = this.y - player.y;
        this.distance = Math.sqrt(dx*dx + dy*dy);
        if (gameFrame % 15 == 0){
            this.frameX++;
            if (this.frameX >= 2) this.frameX = 0;
        }
    }
    draw(){
        /* ctx.fillStyle = 'blue';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill(); */
        if (this.random == 'spawn1'){
            ctx.drawImage(babyLeft, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, this.x - 30, this.y - 20, this.spriteWidth/3, this.spriteHeight/3);
        } else {
            ctx.drawImage(babyRight, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, this.x - 30, this.y - 20, this.spriteWidth/3, this.spriteHeight/3);
        }
        ctx.restore();
    }
}

const babyEat1 = document.createElement('audio');
babyEat1.src = '/static/assets/audio/pop_1.ogg';
const babyEat2 = document.createElement('audio');
babyEat2.src = '/static/assets/audio/pop_2.ogg';

function handleBabies(){
    // run this code every [insert value here] frames
    if (gameFrame % 100 == 0){
        babyArray.push(new babyFish());
    }
    // warning: this isn't a good practice, but it'll do for now
    for (let i = 0; i < babyArray.length; i++){
        babyArray[i].update();
        babyArray[i].draw();
    }
    for (let i = 0; i < babyArray.length; i++){
        if (babyArray[i].y < 0 - babyArray[i].radius * 2){
            babyArray.splice(i, 1);
        }
        if (babyArray[i]){
            if (babyArray[i].distance < babyArray[i].radius + player.radius){
                if (!babyArray[i].counted){
                    if (babyArray[i].sound == 'sound1'){
                        babyEat1.play();
                    } else {
                        babyEat2.play();
                    }
                    score++;
                    babyArray[i].counted = true;
                    babyArray.splice(i, 1);
                }
            }
        }
    }
}

// piranha
const piranhaLeft = new Image();
piranhaLeft.src = '/static/assets/sprite-sheets/piranha-sheet.png'
const piranhaRight = new Image();
piranhaRight.src = '/static/assets/sprite-sheets/piranha-sheet-flipped.png'

class Piranha {
    constructor(){
        this.random = Math.random() <= 0.5 ? 'spawn1' : 'spawn2';
        if (this.random == 'spawn1'){
            this.x = canvas.width + 100;
        } else {
            this.x = canvas.width - 900;
        }
        this.y = Math.random() * (canvas.height - 150) + 90;
        this.radius = 50;
        this.speed = Math.random() * 2 + 2;
        this.frameX = 0;
        this.frameY = 0;
        this.frame = 0;
        this.spriteWidth = 305;
        this.spriteHeight = 310;
        this.distance;
    }
    update(){
        if (this.random == 'spawn1'){
            this.x -= this.speed;
        } else {
            this.x += this.speed;
        }
        const dx = this.x - player.x;
        const dy = this.y - player.y;
        this.distance = Math.sqrt(dx*dx + dy*dy);
        if (gameFrame % 15 == 0){
            this.frameX++;
            if (this.frameX >= 2) this.frameX = 0;
        }
    }
    draw(){
        /* ctx.fillStyle = 'blue';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill(); */
        if (this.random == 'spawn1'){
            ctx.drawImage(piranhaLeft, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, this.x - 50, this.y - 50, this.spriteWidth/3, this.spriteHeight/3);
        } else {
            ctx.drawImage(piranhaRight, this.frameX * this.spriteWidth, this.frameY * this.spriteHeight, this.spriteWidth, this.spriteHeight, this.x - 50, this.y - 50, this.spriteWidth/3, this.spriteHeight/3);
        }
        ctx.restore();
    }
}

const piranhaBite = document.createElement('audio');
piranhaBite.src = '/static/assets/audio/piranha_bite.ogg';

const piranhaArray = [];
function handlePiranhas(){
    // run this code every [insert value here] frames
    if (gameFrame % 100 == 0){
        piranhaArray.push(new Piranha());
    }
    // warning: this isn't a good practice, but it'll do for now
    for (let i = 0; i < piranhaArray.length; i++){
        piranhaArray[i].update();
        piranhaArray[i].draw();
    }
    for (let i = 0; i < piranhaArray.length; i++){
        if (piranhaArray[i].y < 0 - piranhaArray[i].radius * 2){
            piranhaArray.splice(i, 1);
        }
        if (piranhaArray[i]){
            if (piranhaArray[i].distance < piranhaArray[i].radius + player.radius){
                if (!piranhaArray[i].counted){
                    piranhaBite.play();
                    handleGameOver();
                }
            }
        }
    }
}

// game over
function handleGameOver(){
    ctx.fillStyle = 'black';
    ctx.fillText('GAME OVER', 260, 200);
    ctx.fillText('You reached a score of ' + score + '!', 100, 270);
    gameOver = true;
}

// background
var backgroundImages = [];
backgroundImages.length = 4;

//push background images into array
for (var i = 1; i < backgroundImages.length; i++){
    backgroundImages[i] = new Image();
    backgroundImages[i].src = '/static/assets/sprite-sheets/feeding-time-background-f' + i.toString() + '.png';
}

var i = 1;
setInterval(function(){
    i++;
    if(i >= 4){
        i = 1;
    }
},1000)

// animation loop
function animate(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(backgroundImages[i], 0, 0, canvas.width, canvas.height);
    handleBabies();
    handlePiranhas();
    player.update();
    player.draw();
    ctx.fillStyle = 'black';
    ctx.fillText('Score: ' + score, 10, 50);
    //allows us to include periodic events in our game :)
    gameFrame++;
    if (!gameOver) requestAnimationFrame(animate);
}
animate();