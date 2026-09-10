import Phaser from 'phaser';

export const GAME_EVENTS = {
    ENTER_WORLD: 'player:enter_world',
    LEAVE_WORLD: 'player:leave_world'
} as const;

export const EventBus = new Phaser.Events.EventEmitter();