// PHASER
import Phaser from 'phaser';

// DATA
import regionsHighlight from '@/game/data/regions-highligh.json';

// STORE
import { useWorldStore } from '@/game/store/world-store';

export class WorldScene extends Phaser.Scene {
    private newText!: Phaser.GameObjects.Text;

    constructor() {
        super({ key: 'WorldScene' });
    }
    preload() {
    }
    create() {
        const bg = this.add.image(0, 0, 'world-map').setOrigin(0, 0);
        bg.setDisplaySize(1280, 720);

        if (!this.textures.exists('soft-glow')) {
            const canvas = this.textures.createCanvas('soft-glow', 128, 128);
            if (canvas) {
                const ctx = canvas.getContext();
                const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
                grad.addColorStop(0, 'rgba(243, 242, 238, 0.6)');
                grad.addColorStop(0.4, 'rgba(252, 248, 239, 0.4)');
                grad.addColorStop(1, 'rgba(255, 255, 255, 0)');    
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, 128, 128);
                canvas.refresh();
            }
        }

        regionsHighlight.forEach((region)=>{
            const world = useWorldStore.getState().getWorldId(region.id);
            const regionHighlight = this.add
                .circle(region.x, region.y, region.radius, 0xcccc00)
                .setAlpha(0.01)
                .setInteractive({ useHandCursor: true});
                
            const pointLight = this.add.image(region.x, region.y, 'soft-glow')
                .setDisplaySize(region.radius * 2.8, region.radius * 2.8)
                .setBlendMode(Phaser.BlendModes.ADD)
                .setAlpha(0.01);

            const offsetY = region.y + 60 > this.scale.height ? -60 : 50;
            const worldCard = this.add.container(region.x, region.y);
            const background = this.add.image(0, 0, 'world-selector').setDisplaySize(
                150, 85
            ).setAlpha(0.9);

            const worldDescription = this.add.text(
                0, 0, 
                `${world?.worldName}\nLevel: ${world.worldMinLevel}-${world.worldMaxLevel}`, 
                { 
                    fontSize: '14px',
                    align: 'center',
                }
            ).setOrigin(0.5);

            worldCard.add([background, worldDescription]);
            worldCard.setAlpha(0.01);

            regionHighlight.on('pointerover', () => {
                this.tweens.add({
                    targets: pointLight,
                    alpha: 1.0,
                    duration: 200,
                    ease: 'Cubic.easeOut'
                });
                this.tweens.add({
                    targets: worldCard,
                    alpha: 1,
                    y: region.y + offsetY,
                    duration: 150,
                    ease: 'Cubic.easeOut'
                });
            });
            regionHighlight.on('pointerout', () => {
                this.tweens.add({
                    targets: pointLight,
                    alpha: 0.01,
                    duration: 250,
                    ease: 'Cubic.easeOut'
                })
                this.tweens.add({
                    targets: worldCard,
                    alpha: 0.01,
                    delay: 150,
                    y: region.y,
                    duration: 250,
                    ease: 'Cubic.easeOut'
                });
            });
        });

        this.input.keyboard?.once('keydown-SPACE', ()=>{
            this.scene.start('FightScene',{
                creatureName: "Vagabonds",
                creatureLevel: 12
            });
        });
    }
    update() {
    }
}